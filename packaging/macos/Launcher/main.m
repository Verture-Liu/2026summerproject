#import <AppKit/AppKit.h>
#import <Security/Security.h>
#import <sys/socket.h>
#import <netinet/in.h>
#import <arpa/inet.h>
#import <unistd.h>
#import <sys/stat.h>

@interface PaleoRigorDelegate : NSObject <NSApplicationDelegate>
@property(nonatomic, strong) NSTask *backend;
@property(nonatomic, copy) NSString *token;
@property(nonatomic) uint16_t port;
@end

@implementation PaleoRigorDelegate

- (void)applicationDidFinishLaunching:(NSNotification *)notification {
    [NSApp setActivationPolicy:NSApplicationActivationPolicyRegular];
    [self installMenu];
    NSError *error = nil;
    self.token = [self makeToken:&error];
    self.port = [self freeLoopbackPort:&error];
    if (!self.token || self.port == 0 || ![self startBackend:&error]) {
        [self fail:@"PaleoRigor could not start" detail:error.localizedDescription ?: @"Unknown startup error."];
        return;
    }
    [self pollHealth:120];
}

- (void)applicationWillTerminate:(NSNotification *)notification {
    if (self.backend.running) {
        [self.backend terminate];
        [self.backend waitUntilExit];
    }
}

- (void)installMenu {
    NSMenu *main = [[NSMenu alloc] init];
    NSMenuItem *root = [[NSMenuItem alloc] init];
    [main addItem:root];
    NSMenu *submenu = [[NSMenu alloc] initWithTitle:@"PaleoRigor"];
    [submenu addItemWithTitle:@"Quit PaleoRigor" action:@selector(terminate:) keyEquivalent:@"q"];
    root.submenu = submenu;
    NSApp.mainMenu = main;
}

- (NSString *)makeToken:(NSError **)error {
    uint8_t bytes[32];
    if (SecRandomCopyBytes(kSecRandomDefault, sizeof(bytes), bytes) != errSecSuccess) {
        if (error) *error = [NSError errorWithDomain:@"PaleoRigor" code:1 userInfo:@{NSLocalizedDescriptionKey: @"Could not create a secure launch token."}];
        return nil;
    }
    NSData *data = [NSData dataWithBytes:bytes length:sizeof(bytes)];
    NSString *value = [data base64EncodedStringWithOptions:0];
    value = [value stringByReplacingOccurrencesOfString:@"+" withString:@"-"];
    value = [value stringByReplacingOccurrencesOfString:@"/" withString:@"_"];
    return [value stringByReplacingOccurrencesOfString:@"=" withString:@""];
}

- (uint16_t)freeLoopbackPort:(NSError **)error {
    int fd = socket(AF_INET, SOCK_STREAM, 0);
    if (fd < 0) return 0;
    struct sockaddr_in address = {0};
    address.sin_len = sizeof(address);
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = inet_addr("127.0.0.1");
    if (bind(fd, (struct sockaddr *)&address, sizeof(address)) != 0) { close(fd); return 0; }
    socklen_t length = sizeof(address);
    if (getsockname(fd, (struct sockaddr *)&address, &length) != 0) { close(fd); return 0; }
    uint16_t port = ntohs(address.sin_port);
    close(fd);
    return port;
}

- (BOOL)startBackend:(NSError **)error {
    NSURL *executable = [[NSBundle mainBundle].resourceURL URLByAppendingPathComponent:@"backend/PaleoRigorBackend"];
    NSURL *tokenFile = [[NSURL fileURLWithPath:NSTemporaryDirectory()] URLByAppendingPathComponent:[NSString stringWithFormat:@"paleorigor-%@.token", NSUUID.UUID.UUIDString]];
    if (![self.token writeToURL:tokenFile atomically:YES encoding:NSUTF8StringEncoding error:error]) return NO;
    if (chmod(tokenFile.fileSystemRepresentation, 0600) != 0) { [[NSFileManager defaultManager] removeItemAtURL:tokenFile error:nil]; return NO; }
    NSTask *task = [[NSTask alloc] init];
    task.executableURL = executable;
    task.arguments = @[@"--no-browser", @"--port", [NSString stringWithFormat:@"%u", self.port], @"--session-token-file", tokenFile.path];
    task.environment = @{@"HOME": NSHomeDirectory(), @"TMPDIR": NSTemporaryDirectory(), @"LANG": @"en_US.UTF-8"};
    NSFileHandle *nullDevice = [NSFileHandle fileHandleForWritingAtPath:@"/dev/null"];
    task.standardOutput = nullDevice;
    task.standardError = nullDevice;
    __weak typeof(self) weakSelf = self;
    task.terminationHandler = ^(NSTask *ended) { dispatch_async(dispatch_get_main_queue(), ^{ if (NSApp.running) [weakSelf fail:@"PaleoRigor stopped unexpectedly" detail:@"Please reopen the application."]; }); };
    if (![task launchAndReturnError:error]) return NO;
    self.backend = task;
    return YES;
}

- (void)pollHealth:(NSInteger)remaining {
    if (remaining <= 0) { [self fail:@"PaleoRigor could not start" detail:@"The local backend did not become ready."]; return; }
    NSURL *url = [NSURL URLWithString:[NSString stringWithFormat:@"http://127.0.0.1:%u/api/health", self.port]];
    NSMutableURLRequest *request = [NSMutableURLRequest requestWithURL:url];
    [request setValue:self.token forHTTPHeaderField:@"X-PaleoRigor-Token"];
    [[[NSURLSession sharedSession] dataTaskWithRequest:request completionHandler:^(NSData *data, NSURLResponse *response, NSError *error) {
        dispatch_async(dispatch_get_main_queue(), ^{
            if ([(NSHTTPURLResponse *)response statusCode] == 200) [self openBrowser];
            else dispatch_after(dispatch_time(DISPATCH_TIME_NOW, 100 * NSEC_PER_MSEC), dispatch_get_main_queue(), ^{ [self pollHealth:remaining - 1]; });
        });
    }] resume];
}

- (void)openBrowser {
    NSCharacterSet *allowed = NSCharacterSet.alphanumericCharacterSet;
    NSString *encoded = [self.token stringByAddingPercentEncodingWithAllowedCharacters:allowed];
    NSURL *url = [NSURL URLWithString:[NSString stringWithFormat:@"http://127.0.0.1:%u/#token=%@", self.port, encoded]];
    [[NSWorkspace sharedWorkspace] openURL:url];
}

- (void)fail:(NSString *)title detail:(NSString *)detail {
    NSAlert *alert = [[NSAlert alloc] init];
    alert.messageText = title; alert.informativeText = detail; alert.alertStyle = NSAlertStyleCritical;
    [alert runModal]; [NSApp terminate:nil];
}
@end

int main(int argc, const char *argv[]) {
    @autoreleasepool {
        NSApplication *app = NSApplication.sharedApplication;
        PaleoRigorDelegate *delegate = [[PaleoRigorDelegate alloc] init];
        app.delegate = delegate;
        [app run];
    }
    return 0;
}
