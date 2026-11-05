package services;

import db.Database;
import models.Attendance;
import models.Marks;
import models.Student;

public class StudentService {
    private final Database database;

    public StudentService(Database database) {
        this.database = database;
    }

    public void addStudent(Student student) {
        database.insert("students", student.getId(), student);
    }

    public Student getStudent(String id) {
        return (Student) database.find("students", id);
    }

    public void saveMarks(Marks marks) {
        // Student marks are stored in the "marks" table of the Database
        database.insert("marks", marks.getStudentId(), marks);
    }

    public Marks getMarks(String studentId) {
        return (Marks) database.find("marks", studentId);
    }

    public void recordAttendance(String studentId, boolean present) {
        Attendance attendance = (Attendance) database.find("attendance", studentId);
        if (attendance == null) {
            attendance = new Attendance(studentId);
        }
        attendance.markDay(present);
        database.insert("attendance", studentId, attendance);
    }
}
