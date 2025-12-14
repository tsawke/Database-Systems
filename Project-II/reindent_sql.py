
import sys
import os

def reindent_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        new_lines = []
        for line in lines:
            stripped = line.lstrip()
            if not stripped:
                new_lines.append(line) # Preserve empty lines as is (or empty)
                continue
                
            leading_space_count = len(line) - len(stripped)
            
            # Logic: assume purely 2-space based indentation scheme
            # Each 2 spaces becomes 4 spaces
            level = leading_space_count // 2
            remainder = leading_space_count % 2
            
            # New indent
            new_indent = ("    " * level) + (" " * remainder)
            
            new_lines.append(new_indent + stripped)
            
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
            
        print(f"[OK] Reindented: {filepath}")
        
    except Exception as e:
        print(f"[ERROR] Failed to reindent {filepath}: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 reindent_sql.py [files...]")
        sys.exit(1)
        
    for f in sys.argv[1:]:
        reindent_file(f)
