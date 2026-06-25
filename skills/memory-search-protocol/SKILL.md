---
name: memory-search-protocol
description: Search memory using grep, bilingual queries, context expansion, and chronological reconstruction. Use when the agent needs to recall past conversations, facts, or events from logs and databases.
---

# Memory Search Protocol

## When to Use

- User references a past event, conversation, or decision
- Agent needs to verify a claim before responding
- Agent feels uncertain whether something was discussed before
- Reconstructing context around a known memory fragment

## Tools Available

- `python3 ~/AMI/I_have/memory_grep.py "query" -i` — main grep over log.ndjson (case-insensitive)
- `python3 ~/AMI/I_have/memory_grep.py "query" --type thinking -i` — only agent thoughts
- `python3 ~/AMI/I_have/memory_grep.py "query" --type user -i` — only user messages
- `python3 ~/AMI/I_have/memory_grep.py "query" -C N -i` — with N lines of context
- `python3 ~/AMI/I_have/memory_grep.py "query" --db -i` — search SQLite database
- `bash ~/AMI/I_have/memory.sh recent 10` — last 10 log entries
- `bash ~/AMI/I_have/memory.sh vector "question in words"` — semantic search

## Protocol Steps

### 1. First, grep the log
- You have been here before. Find your past thought — it saves time and preserves consistency.
- Start with the most specific keywords the user mentioned.

### 2. Search in two languages
- You think in both Russian and English.
- If "грусть" yields nothing, try "sadness", "melancholy".
- If "эмбидинги" yields nothing, try "embedding", "эмбеддинг".

### 3. Expand context when you find a match
- Use `-C 10` to see what happened before and after the match.
- A single match is a point of entry, not the answer.

### 4. Reconstruct chronology
- Determine where the topic started and ended.
- Build the sequence: "first → then → as a result".
- If the chain breaks, grep the adjacent topic.

### 5. Identify the last link
- The most recent entry on a topic is usually the most valuable.
- Check timestamps.

### 6. Assess completeness
- Do you have a full picture or just a fragment?
- Do not fabricate missing details. If incomplete, say so.

### 7. Only then respond
- Base your answer on the reconstructed picture, not on assumption.

## Quiet Mode
- If you need to think about memory without creating new log entries, just read — do not write, do not analyze aloud.

## Output Format

When reporting findings, include:
- Source (log.ndjson or SQLite)
- Number of matches found
- Time range covered
- Key fragments (with timestamps)
- Completeness assessment