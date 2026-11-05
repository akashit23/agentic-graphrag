package auth;

import db.Database;

public class AuthService {
    private final Database database;

    public AuthService(Database database) {
        this.database = database;
    }

    public void register(String username, String password) {
        if (!validatePassword(password)) {
            throw new IllegalArgumentException("Weak password");
        }
        database.insert("users", username, password);
    }

    public boolean validatePassword(String password) {
        return password != null && password.length() >= 8;
    }

    public boolean authenticate(String username, String password) {
        Object stored = database.find("users", username);
        return stored != null && stored.equals(password);
    }
}
