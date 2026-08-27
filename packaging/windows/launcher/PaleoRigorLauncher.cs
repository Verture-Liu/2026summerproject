using System.Diagnostics;
using System.Net;
using System.Net.Http.Headers;
using System.Net.Sockets;
using System.Security.Cryptography;
using System.Text;
using System.Windows.Forms;

namespace PaleoRigor;

internal sealed class PaleoRigorApplication : ApplicationContext
{
    private readonly NotifyIcon trayIcon;
    private Process? backend;
    private string? browserUrl;
    private string? tokenFile;
    private bool exiting;

    public PaleoRigorApplication()
    {
        var menu = new ContextMenuStrip();
        menu.Items.Add("Open PaleoRigor", null, (_, _) => OpenBrowser());
        menu.Items.Add("Exit", null, (_, _) => ExitApplication());
        trayIcon = new NotifyIcon
        {
            Text = "PaleoRigor research prototype",
            Icon = System.Drawing.SystemIcons.Application,
            ContextMenuStrip = menu,
            Visible = true,
        };
        trayIcon.DoubleClick += (_, _) => OpenBrowser();
        _ = StartAsync();
    }

    private async Task StartAsync()
    {
        try
        {
            var appRoot = AppContext.BaseDirectory;
            var backendPath = Path.Combine(appRoot, "backend", "PaleoRigorBackend.exe");
            var toolRoot = Path.Combine(appRoot, "backend", "_internal", "research_agent", "tools");
            if (!File.Exists(backendPath) || !Directory.Exists(toolRoot))
                throw new FileNotFoundException("The installed backend or tool bundle is missing.");

            var localData = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
            var runtimeDirectory = Path.Combine(localData, "PaleoRigor", "runtime");
            Directory.CreateDirectory(runtimeDirectory);
            var token = Base64Url(RandomNumberGenerator.GetBytes(32));
            tokenFile = Path.Combine(runtimeDirectory, $"launch-{Guid.NewGuid():N}.token");
            File.WriteAllText(tokenFile, token, new UTF8Encoding(false));
            var port = FindFreePort();

            var start = new ProcessStartInfo(backendPath)
            {
                UseShellExecute = false,
                CreateNoWindow = true,
                WorkingDirectory = appRoot,
            };
            start.ArgumentList.Add("--no-browser");
            start.ArgumentList.Add("--port");
            start.ArgumentList.Add(port.ToString());
            start.ArgumentList.Add("--session-token-file");
            start.ArgumentList.Add(tokenFile);
            start.Environment["PALEORIGOR_TOOL_ROOT"] = toolRoot;
            backend = Process.Start(start) ?? throw new InvalidOperationException("The local backend did not start.");
            backend.EnableRaisingEvents = true;
            backend.Exited += (_, _) =>
            {
                if (!exiting)
                    Fail("PaleoRigor stopped unexpectedly", "Close and reopen the application. A local log may contain more information.");
            };

            browserUrl = $"http://127.0.0.1:{port}/#token={Uri.EscapeDataString(token)}";
            await WaitForHealthAsync(port, token, TimeSpan.FromSeconds(45));
            OpenBrowser();
        }
        catch (Exception error)
        {
            Fail("PaleoRigor could not start", error.Message);
        }
        finally
        {
            if (tokenFile is not null && File.Exists(tokenFile)) File.Delete(tokenFile);
        }
    }

    private static string Base64Url(byte[] bytes) =>
        Convert.ToBase64String(bytes).TrimEnd('=').Replace('+', '-').Replace('/', '_');

    private static int FindFreePort()
    {
        var listener = new TcpListener(IPAddress.Loopback, 0);
        listener.Start();
        var port = ((IPEndPoint)listener.LocalEndpoint).Port;
        listener.Stop();
        return port;
    }

    private static async Task WaitForHealthAsync(int port, string token, TimeSpan timeout)
    {
        using var client = new HttpClient { Timeout = TimeSpan.FromSeconds(2) };
        client.DefaultRequestHeaders.Add("X-PaleoRigor-Token", token);
        var deadline = DateTime.UtcNow + timeout;
        while (DateTime.UtcNow < deadline)
        {
            try
            {
                using var response = await client.GetAsync($"http://127.0.0.1:{port}/api/health");
                if (response.StatusCode == HttpStatusCode.OK) return;
            }
            catch (HttpRequestException) { }
            catch (TaskCanceledException) { }
            await Task.Delay(250);
        }
        throw new TimeoutException("The local backend did not become ready within 45 seconds.");
    }

    private void OpenBrowser()
    {
        if (browserUrl is null) return;
        Process.Start(new ProcessStartInfo(browserUrl) { UseShellExecute = true });
    }

    private void Fail(string title, string detail)
    {
        MessageBox.Show(detail, title, MessageBoxButtons.OK, MessageBoxIcon.Error);
        ExitApplication();
    }

    private void ExitApplication()
    {
        if (exiting) return;
        exiting = true;
        trayIcon.Visible = false;
        if (backend is { HasExited: false })
        {
            backend.Kill(entireProcessTree: true);
            backend.WaitForExit(5000);
        }
        if (tokenFile is not null && File.Exists(tokenFile)) File.Delete(tokenFile);
        trayIcon.Dispose();
        ExitThread();
    }
}

internal static class Program
{
    [STAThread]
    private static void Main()
    {
        ApplicationConfiguration.Initialize();
        Application.Run(new PaleoRigorApplication());
    }
}
