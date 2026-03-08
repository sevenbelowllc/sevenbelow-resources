# No Mock Data Policy

**Trigger:** Any work involving UI components, data display, forms, or testing

## Rule (NON-NEGOTIABLE)

**NEVER use inline mock data arrays in components.**

### ❌ FORBIDDEN Patterns

```typescript
// NEVER DO THIS
const mockUsers = [{ id: '1', name: 'Test User' }];
const [items, setItems] = useState([{ id: '1', title: 'Fake Item' }]);
const MOCK_DATA = [...];
const sampleData = [...];
const dummyData = [...];
const testData = [...];
```

### ✅ REQUIRED Patterns

```typescript
// ALWAYS DO THIS - Use GraphQL hooks
import { useUsers } from '../api/hooks';

const { users, loading, error } = useUsers();

if (loading) return <LoadingSpinner />;
if (error) return <ErrorMessage error={error} />;
if (users.length === 0) return <EmptyState />;
```

## If Data Is Needed For Development

**Create seed data in the database**, not mock arrays in components:

1. Add seed data to `compliance-core/src/db/seeds/`
2. Run `npm run seed` to populate the database
3. Components fetch real data via GraphQL

## Why This Matters

1. **Mock data rots** — Components with mock data break silently when schemas change
2. **False confidence** — Mock data hides integration bugs
3. **Duplicate work** — You write mock data AND seed data anyway
4. **Production parity** — Empty states and loading states must work correctly

## Checklist Before Committing

- [ ] No `mock`, `Mock`, `MOCK` strings in component files
- [ ] No `useState([{...}])` with inline object arrays
- [ ] Components use GraphQL hooks from `features/{domain}/api/hooks.ts`
- [ ] Loading states handled
- [ ] Empty states handled
- [ ] If dev data needed, it's in seed files

## Applies To

- All React components
- All pages
- All features
- All tests (use GraphQL mocking, not inline data)
