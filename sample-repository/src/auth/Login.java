package auth;

import services.StudentService;

public class Login {
    private final AuthService authService;
    private final StudentService studentService;

    public Login(AuthService authService, StudentService studentService) {
        this.authService = authService;
        this.studentService = studentService;
    }

    public boolean login(String username, String password) {
        return authService.authenticate(username, password);
    }

    public void showStudent(String id) {
        System.out.println(studentService.getStudent(id).getName());
    }
}
