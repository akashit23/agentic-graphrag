import auth.AuthService;
import auth.Login;
import db.Database;
import models.Marks;
import models.Student;
import services.StudentService;

public class Main {
    public static void main(String[] args) {
        Database database = new Database();
        AuthService authService = new AuthService(database);
        StudentService studentService = new StudentService(database);
        Login login = new Login(authService, studentService);

        authService.register("admin", "secret123");
        studentService.addStudent(new Student("S1", "Asha"));
        studentService.saveMarks(new Marks("S1", "Maths", 88));
        studentService.recordAttendance("S1", true);
        System.out.println(login.login("admin", "secret123"));
    }
}
