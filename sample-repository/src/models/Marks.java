package models;

public class Marks {
    private final String studentId;
    private final String subject;
    private final int score;

    public Marks(String studentId, String subject, int score) {
        this.studentId = studentId;
        this.subject = subject;
        this.score = score;
    }

    public String getStudentId() {
        return studentId;
    }

    public int getScore() {
        return score;
    }

    public boolean isPassing() {
        return score >= 40;
    }
}
