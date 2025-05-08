# Supabase Integration

## Setup

1. Create an account at https://supabase.com
2. Create a new project and copy your API URL and anon/public key
3. Replace `.env` with:

```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
```

4. Create these tables in Supabase:

### `profiles`
| Column        | Type     | Notes          |
|---------------|----------|----------------|
| name          | text     | primary key    |
| games_played  | int      |                |
| wins          | int      |                |
| money_earned  | int      |                |
| cards_collected | int    |                |

### `leaderboard`
| Column    | Type | Notes |
|-----------|------|-------|
| name      | text |       |
| money     | int  |       |
| cards     | int  |       |
| badges    | int  |       |

Ensure both tables have Row Level Security turned **off** for public testing (or set policies if going secure).