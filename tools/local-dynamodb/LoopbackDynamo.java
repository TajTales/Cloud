import java.lang.reflect.Field;
import org.eclipse.jetty.server.Server;
import org.eclipse.jetty.server.ServerConnector;
import software.amazon.dynamodb.services.local.main.ServerRunner;

// DynamoDB Local 3.3.2 has no bind-host CLI option. Limit its embedded Jetty
// connector before start, without modifying the vendor JAR. Fail closed if the
// pinned distribution changes the expected embedding API.
class LoopbackDynamo {
    public static void main(String[] args) throws Exception {
        var local = ServerRunner.createServerFromCommandLineArgs(args);
        Field field = local.getClass().getDeclaredField("server");
        field.setAccessible(true);
        Server server = (Server) field.get(local);
        if (server.getConnectors().length == 0) {
            throw new IllegalStateException("No local database connector");
        }
        for (var connector : server.getConnectors()) {
            if (!(connector instanceof ServerConnector)) {
                throw new IllegalStateException("Unexpected database connector");
            }
            ((ServerConnector) connector).setHost("127.0.0.1");
        }
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            try { local.stop(); } catch (Exception ignored) { }
        }));
        local.start();
        local.join();
    }
}
