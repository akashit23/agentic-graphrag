package db;

import java.util.HashMap;
import java.util.Map;

public class Database {
    private final Map<String, Object> tables = new HashMap<>();

    public void insert(String table, String key, Object value) {
        tables.put(table + ":" + key, value);
    }

    public Object find(String table, String key) {
        return tables.get(table + ":" + key);
    }

    public void delete(String table, String key) {
        tables.remove(table + ":" + key);
    }
}
