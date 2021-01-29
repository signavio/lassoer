import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.FileInputStream;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.Statement;
import java.util.Properties;
import java.util.List;
import java.util.ArrayList;
import java.util.StringTokenizer;

public class Extract{
    public static void main(String[] args) {
        String pathToEnvFile = "./.env";
        String driverClassName = "jdbc:saperp:"; // Default to SAP ERP system
        String[] options = String.join(" ", args).split("-");
        for (String opt: options) {
            if (opt.startsWith("h")) {
                helpMessage();
                System.exit(0);
            }
            if (opt.startsWith("f")) {
                pathToEnvFile = opt.split(" ")[1];
            }
            if (opt.startsWith("r")) {
                driverClassName = opt.split(" ")[1];
            }
        }

        Properties prop = new Properties();
        try(FileInputStream inputStream = new FileInputStream(pathToEnvFile)) {
            prop.load(inputStream);
        } catch (Throwable t) {
            System.out.println(t);
        }
        prop.list(System.out);

        List<String> tokens = new ArrayList<>();
        BufferedReader br = null;
        String query = "";
        try {
            br = new BufferedReader(new InputStreamReader(System.in));
            StringTokenizer st = new StringTokenizer(br.readLine());
 
            while (st != null && st.hasMoreElements()) {
                tokens.add(st.nextToken());
            }
            query = String.join(" ", tokens);
        } catch (Throwable t) {
            System.out.println(t);
        }
        try {
            Connection conn = DriverManager.getConnection(driverClassName, prop);
            Statement stmt = conn.createStatement();
            boolean ret = stmt.execute(query);
            if (ret) {
                ResultSet rs = stmt.getResultSet();
                for(int i=1; i<=rs.getMetaData().getColumnCount(); i++) {
                    System.out.print(rs.getMetaData().getColumnName(i) + "\t");
                }
                System.out.println();
                while(rs.next()) {
                    for(int i=1; i<=rs.getMetaData().getColumnCount(); i++) {
                        if (i == rs.getMetaData().getColumnCount()) {
                            System.out.print(rs.getString(i));
                        } else {
                            System.out.print(rs.getString(i) + "\t");
                        }
                    }
                    System.out.println();
                }
            }
        } catch (Throwable t) {
            System.out.println(t);
        }
    }
    private static void helpMessage() {
        String msg = new StringBuilder()
            .append("Usage: extract [options] [FILE]\n\n")
            .append("Extract data from a source system and output result to STDOUT\n\n")
            .append("Options:\n\t-f\tenvironment file containing connection options\n")
            .append("\t-r\tdriver class name provided to the driver manager\n")
            .append("\t-h\tprint this help message\n\n")
            .append("With no FILE, or when FILE is -, read from standard input.")
            .toString();
        System.out.println(msg);
    }
}
