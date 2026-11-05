package models;

public class Attendance {
    private final String studentId;
    private int daysPresent;
    private int totalDays;

    public Attendance(String studentId) {
        this.studentId = studentId;
    }

    public void markDay(boolean present) {
        totalDays++;
        if (present) {
            daysPresent++;
        }
    }

    public double percentage() {
        return totalDays == 0 ? 0 : (daysPresent * 100.0) / totalDays;
    }
}
