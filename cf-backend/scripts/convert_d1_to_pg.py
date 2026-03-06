#!/usr/bin/env python3
"""
convert_d1_to_pg.py
====================
Konversi SQLite D1 export SQL ke PostgreSQL-compatible SQL.
Transformasi:
  - Hapus PRAGMA, CREATE TABLE, CREATE INDEX (sudah ada via Drizzle)
  - Ganti backtick identifier ke double-quote
  - Konversi boolean columns (0/1 -> false/true)
  - Ganti INSERT OR IGNORE -> INSERT ... ON CONFLICT DO NOTHING
"""

import re
import sys
import os

INPUT  = "migration_backup/d1_export.sql"
OUTPUT = "migration_backup/pg_import.sql"

# Kolom boolean per tabel (dari schema.ts)
BOOLEAN_COLUMNS = {
    "dramas":       ["is_vip", "is_featured", "is_active"],
    "episodes":     ["is_vip", "is_active"],
    "users":        ["is_guest", "vip_status", "notify_episodes", "notify_coins", "notify_system", "is_active"],
    "subtitles":    ["is_default"],
    "achievements": ["is_active"],
    "collections":  ["notify_new_episode"],
    "notifications":["read"],
    "categories":   [],
    "seasons":      [],
    "watchlist":    [],
    "favorites":    [],
    "watch_history":[],
    "coin_transactions": [],
    "daily_rewards": [],
    "user_achievements": [],
}

# Kolom timestamp per tabel (Unix integer -> to_timestamp)
TIMESTAMP_COLUMNS = {
    "dramas":        ["release_date", "created_at", "updated_at"],
    "episodes":      ["release_date", "created_at", "updated_at"],
    "users":         ["vip_expiry", "last_check_in", "created_at", "updated_at"],
    "subtitles":     ["created_at"],
    "achievements":  ["created_at"],
    "collections":   ["added_at"],
    "daily_rewards": ["claimed_at"],
    "notifications": ["created_at"],
    "seasons":       ["release_date", "created_at", "updated_at"],
    "watchlist":     ["added_at"],
    "favorites":     ["added_at"],
    "watch_history": ["watched_at"],
    "coin_transactions": ["created_at"],
    "user_achievements": ["unlocked_at"],
    "categories":    [],
}

def fix_identifiers(sql: str) -> str:
    """Ganti backtick ke double-quote untuk identifiers."""
    return sql.replace('`', '"')

def parse_columns(col_str: str) -> list:
    """Parse '(col1, col2, ...)' ke list kolom."""
    col_str = col_str.strip().strip('()')
    return [c.strip().strip('"').strip("'") for c in col_str.split(',')]

def parse_values_list(values_str: str) -> list:
    """Parse VALUES (...), (...) ke list of value-tuples."""
    # Simple parser - handle quoted strings with commas
    results = []
    depth = 0
    current = []
    in_quote = False
    quote_char = None
    i = 0
    buffer = ""
    
    # Find all (...) groups
    while i < len(values_str):
        c = values_str[i]
        if not in_quote and c in ("'", '"'):
            in_quote = True
            quote_char = c
            buffer += c
        elif in_quote and c == quote_char:
            if i + 1 < len(values_str) and values_str[i+1] == quote_char:
                buffer += c + quote_char
                i += 2
                continue
            in_quote = False
            buffer += c
        elif not in_quote and c == '(':
            depth += 1
            if depth == 1:
                buffer = ""
            else:
                buffer += c
        elif not in_quote and c == ')':
            depth -= 1
            if depth == 0:
                results.append(buffer)
                buffer = ""
            else:
                buffer += c
        else:
            buffer += c
        i += 1
    return results

def split_values(values_str: str) -> list:
    """Split comma-separated values dengan respect quoted strings."""
    result = []
    depth = 0
    in_quote = False
    quote_char = None
    current = ""
    i = 0
    while i < len(values_str):
        c = values_str[i]
        if not in_quote and c in ("'",):
            in_quote = True
            quote_char = c
            current += c
        elif in_quote and c == quote_char:
            if i + 1 < len(values_str) and values_str[i+1] == quote_char:
                current += c + quote_char
                i += 2
                continue
            in_quote = False
            current += c
        elif not in_quote and c == ',':
            result.append(current.strip())
            current = ""
        else:
            current += c
        i += 1
    if current.strip():
        result.append(current.strip())
    return result

def convert_values(table: str, columns: list, values_str: str) -> str:
    """Konversi boolean (0/1) dan timestamp (int -> to_timestamp) per tabel."""
    bool_cols = set(BOOLEAN_COLUMNS.get(table, []))
    ts_cols = set(TIMESTAMP_COLUMNS.get(table, []))
    if not bool_cols and not ts_cols:
        return values_str

    bool_indices = {i for i, col in enumerate(columns) if col in bool_cols}
    ts_indices   = {i for i, col in enumerate(columns) if col in ts_cols}

    val_groups = parse_values_list(values_str)
    new_groups = []
    for group in val_groups:
        vals = split_values(group)
        new_vals = []
        for i, v in enumerate(vals):
            stripped = v.strip()
            if i in bool_indices:
                if stripped == '0': v = 'false'
                elif stripped == '1': v = 'true'
            elif i in ts_indices:
                # Unix integer -> to_timestamp()
                if stripped.lstrip('-').isdigit() and stripped != 'NULL':
                    v = f'to_timestamp({stripped})'
            new_vals.append(v)
        new_groups.append("(" + ", ".join(new_vals) + ")")

    return ", ".join(new_groups)

def process():
    if not os.path.exists(INPUT):
        print(f"❌ File tidak ditemukan: {INPUT}")
        sys.exit(1)
    
    print(f"📖 Reading {INPUT}...")
    with open(INPUT, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    output_lines = ["-- PostgreSQL Import (converted from SQLite D1 export)",
                    "-- Generated by convert_d1_to_pg.py",
                    "SET session_replication_role = replica; -- disable FK checks during import\n"]
    
    skip_patterns = [
        r'^\s*PRAGMA',
        r'^\s*CREATE TABLE',
        r'^\s*CREATE UNIQUE INDEX',
        r'^\s*CREATE INDEX',
        r'^\s*--',
        r'^\s*$',
    ]
    
    i = 0
    insert_count = 0
    while i < len(lines):
        line = lines[i]
        
        # Lewati baris yang tidak diperlukan
        skip = any(re.match(p, line, re.IGNORECASE) for p in skip_patterns)
        if skip:
            i += 1
            continue
        
        # Kumpulkan INSERT statement (bisa multi-line)
        if re.match(r'^\s*INSERT', line, re.IGNORECASE):
            # Kumpulkan sampai semicolon
            stmt = line
            while not stmt.rstrip().endswith(';') and i + 1 < len(lines):
                i += 1
                stmt += '\n' + lines[i]
            
            # Fix identifiers
            stmt = fix_identifiers(stmt)
            
            # Ganti INSERT OR IGNORE -> INSERT
            stmt = re.sub(r'INSERT OR (?:IGNORE|REPLACE)\s+', 'INSERT ', stmt, flags=re.IGNORECASE)
            
            # Tambah ON CONFLICT DO NOTHING sebelum ;
            stmt = re.sub(r'\s*;\s*$', ' ON CONFLICT DO NOTHING;', stmt)
            
            # Extract table name dan columns untuk konversi boolean
            match = re.match(
                r'INSERT INTO\s+"?(\w+)"?\s*\(([^)]+)\)\s*VALUES\s*(.*?)\s*ON CONFLICT',
                stmt, re.IGNORECASE | re.DOTALL
            )
            if match:
                table_name = match.group(1)
                col_str = match.group(2)
                val_str = match.group(3)
                columns = parse_columns(col_str)
                new_vals = convert_values(table_name, columns, val_str)
                stmt = stmt[:match.start(3)] + new_vals + stmt[match.end(3):]
            
            output_lines.append(stmt)
            insert_count += 1
        
        i += 1
    
    output_lines.append("\nSET session_replication_role = DEFAULT;")
    
    print(f"✅ Converted {insert_count} INSERT statements")
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))
    print(f"💾 Saved to {OUTPUT}")
    print(f"📦 Size: {os.path.getsize(OUTPUT) / 1024:.1f} KB")

if __name__ == '__main__':
    process()
