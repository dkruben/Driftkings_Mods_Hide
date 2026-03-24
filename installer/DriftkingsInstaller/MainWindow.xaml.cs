using Microsoft.Win32;
using System.Collections.ObjectModel;
using System.Diagnostics;
using System.IO;
using System.IO.Compression;
using System.Reflection;
using System.Text.Json;
using System.Text.RegularExpressions;
using System.Windows;
using System.Windows.Controls;
using System.Xml.Linq;
using Forms = System.Windows.Forms;
using WpfMessageBox = System.Windows.MessageBox;

namespace DriftkingsInstaller;

public partial class MainWindow : Window
{
    private readonly ObservableCollection<PackageItem> _packages = new();
    private readonly ObservableCollection<GameInstallation> _installations = new();
    private InstallerManifest _manifest = new();
    private string _selectedRegion = "EU";
    private bool _isInstalling;

    public MainWindow()
    {
        InitializeComponent();
        PackagesListBox.ItemsSource = _packages;
        DetectedInstallationsComboBox.ItemsSource = _installations;
        Loaded += MainWindow_Loaded;
    }

    private void MainWindow_Loaded(object sender, RoutedEventArgs e)
    {
        try
        {
            _manifest = LoadManifest();
            TitleText.Text = _manifest.Title;
            SubtitleText.Text = $"Game version {_manifest.GameVersion} | Package {_manifest.PackageVersion}";
            GameVersionText.Text = _manifest.GameVersion;
            PackageCountText.Text = _manifest.Packages.Count.ToString();

            foreach (var package in _manifest.Packages.OrderBy(x => x.IsMaintenance ? 0 : 1).ThenBy(x => x.DisplayName))
            {
                var item = new PackageItem(package);
                item.PropertyChanged += (_, _) =>
                {
                    UpdateSelectionSummary();
                    ValidateSelectedPath();
                };
                _packages.Add(item);
            }

            EuRegionButton.IsChecked = true;
            RefreshDetectedInstallations();
            if (_installations.Count == 0)
            {
                InstallPathTextBox.Text = GuessGameRoot(_selectedRegion);
            }

            UpdateSelectionSummary();
            ValidateSelectedPath();
        }
        catch (Exception ex)
        {
            WpfMessageBox.Show($"Falha ao carregar o instalador.\n\n{ex.Message}", "Driftkings Installer", MessageBoxButton.OK, MessageBoxImage.Error);
            Close();
        }
    }

    private static InstallerManifest LoadManifest()
    {
        using var stream = OpenEmbeddedResource("payload_manifest.json");
        return JsonSerializer.Deserialize<InstallerManifest>(stream) ?? new InstallerManifest();
    }

    private static Stream OpenEmbeddedResource(string resourceName)
    {
        var assembly = Assembly.GetExecutingAssembly();
        var match = assembly.GetManifestResourceNames()
            .FirstOrDefault(name => name.EndsWith(resourceName.Replace('/', '.').Replace('\\', '.'), StringComparison.OrdinalIgnoreCase));

        if (match is null)
        {
            throw new FileNotFoundException($"Embedded resource not found: {resourceName}");
        }

        return assembly.GetManifestResourceStream(match)
               ?? throw new FileNotFoundException($"Unable to open embedded resource: {resourceName}");
    }

    private void RegionButton_Checked(object sender, RoutedEventArgs e)
    {
        if (sender == EuRegionButton)
        {
            _selectedRegion = "EU";
            NaRegionButton.IsChecked = false;
        }
        else
        {
            _selectedRegion = "NA";
            EuRegionButton.IsChecked = false;
        }

        RefreshDetectedInstallations();
        if (_installations.Count == 0 && (string.IsNullOrWhiteSpace(InstallPathTextBox.Text) || !Directory.Exists(InstallPathTextBox.Text)))
        {
            InstallPathTextBox.Text = GuessGameRoot(_selectedRegion);
        }

        FooterTextBlock.Text = $"Destino: raiz do jogo {_selectedRegion}. O instalador valida a versao antes de copiar os mods.";
        ValidateSelectedPath();
    }

    private void RefreshDetectionsButton_Click(object sender, RoutedEventArgs e)
    {
        RefreshDetectedInstallations();
    }

    private void DetectedInstallationsComboBox_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (DetectedInstallationsComboBox.SelectedItem is not GameInstallation installation)
        {
            return;
        }

        InstallPathTextBox.Text = installation.RootPath;
        if (installation.Region == "EU" || installation.Region == "NA")
        {
            _selectedRegion = installation.Region;
            EuRegionButton.IsChecked = installation.Region == "EU";
            NaRegionButton.IsChecked = installation.Region == "NA";
        }

        ValidateSelectedPath();
    }

    private void InstallPathTextBox_TextChanged(object sender, TextChangedEventArgs e)
    {
        ValidateSelectedPath();
    }

    private void RefreshDetectedInstallations()
    {
        _installations.Clear();
        foreach (var installation in DetectInstallations(_selectedRegion))
        {
            _installations.Add(installation);
        }

        if (_installations.Count > 0)
        {
            DetectedInstallationsComboBox.SelectedIndex = 0;
            StatusTextBlock.Text = $"Encontradas {_installations.Count} instalacoes do cliente.";
        }
        else
        {
            StatusTextBlock.Text = "Nenhuma instalacao detetada automaticamente. Pode escolher a pasta manualmente.";
        }
    }

    private IEnumerable<GameInstallation> DetectInstallations(string region)
    {
        var seen = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

        foreach (var path in GetRegistryInstallPaths())
        {
            var installation = CreateInstallation(path, "Registry");
            if (installation is not null && MatchesRegion(installation, region) && seen.Add(installation.RootPath))
            {
                yield return installation;
            }
        }

        foreach (var path in GetCommonInstallPaths())
        {
            var installation = CreateInstallation(path, "Common path");
            if (installation is not null && MatchesRegion(installation, region) && seen.Add(installation.RootPath))
            {
                yield return installation;
            }
        }

        foreach (var path in ScanDrivesForGameFolders())
        {
            var installation = CreateInstallation(path, "Drive scan");
            if (installation is not null && MatchesRegion(installation, region) && seen.Add(installation.RootPath))
            {
                yield return installation;
            }
        }
    }

    private static IEnumerable<string> GetRegistryInstallPaths()
    {
        const string uninstallPath = @"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall";
        var roots = new[] { Registry.CurrentUser, Registry.LocalMachine };

        foreach (var root in roots)
        {
            foreach (var basePath in new[] { uninstallPath, @"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall" })
            {
                using var key = root.OpenSubKey(basePath);
                if (key is null)
                {
                    continue;
                }

                foreach (var subKeyName in key.GetSubKeyNames())
                {
                    using var subKey = key.OpenSubKey(subKeyName);
                    var displayName = subKey?.GetValue("DisplayName") as string;
                    var installLocation = subKey?.GetValue("InstallLocation") as string;
                    if (string.IsNullOrWhiteSpace(displayName) || string.IsNullOrWhiteSpace(installLocation))
                    {
                        continue;
                    }

                    if (displayName.IndexOf("World of Tanks", StringComparison.OrdinalIgnoreCase) >= 0)
                    {
                        yield return installLocation.Trim().Trim('"');
                    }
                }
            }
        }
    }

    private static IEnumerable<string> GetCommonInstallPaths()
    {
        return new[]
        {
            @"C:\Games\World_of_Tanks",
            @"C:\Games\World_of_Tanks_EU",
            @"C:\Games\World_of_Tanks_NA",
            @"D:\Games\World_of_Tanks",
            @"D:\Games\World_of_Tanks_EU",
            @"D:\Games\World_of_Tanks_NA",
            @"C:\Program Files (x86)\World_of_Tanks",
            @"C:\Program Files (x86)\World_of_Tanks_EU",
            @"C:\Program Files (x86)\World_of_Tanks_NA"
        };
    }

    private static IEnumerable<string> ScanDrivesForGameFolders()
    {
        foreach (var drive in DriveInfo.GetDrives().Where(d => d.IsReady && d.DriveType == DriveType.Fixed))
        {
            string[] rootsToCheck;
            try
            {
                rootsToCheck = Directory.GetDirectories(drive.RootDirectory.FullName, "World_of_Tanks*", SearchOption.TopDirectoryOnly);
            }
            catch
            {
                continue;
            }

            foreach (var path in rootsToCheck)
            {
                yield return path;
            }

            foreach (var gamesDir in new[] { Path.Combine(drive.RootDirectory.FullName, "Games"), Path.Combine(drive.RootDirectory.FullName, "Wargaming.net") })
            {
                if (!Directory.Exists(gamesDir))
                {
                    continue;
                }

                string[] dirs;
                try
                {
                    dirs = Directory.GetDirectories(gamesDir, "World_of_Tanks*", SearchOption.TopDirectoryOnly);
                }
                catch
                {
                    continue;
                }

                foreach (var path in dirs)
                {
                    yield return path;
                }
            }
        }
    }

    private GameInstallation? CreateInstallation(string path, string source)
    {
        if (string.IsNullOrWhiteSpace(path) || !Directory.Exists(path) || !IsLikelyGameRoot(path))
        {
            return null;
        }

        var version = DetectGameVersion(path);
        return new GameInstallation
        {
            RootPath = path,
            Region = DetectRegionFromPath(path),
            DetectedVersion = version,
            VersionMatches = !string.IsNullOrWhiteSpace(version) && version == _manifest.GameVersion,
            Source = source
        };
    }

    private static bool MatchesRegion(GameInstallation installation, string region)
    {
        return installation.Region == "Unknown" || installation.Region == region;
    }

    private static string GuessGameRoot(string region)
    {
        var candidates = region == "NA"
            ? new[]
            {
                @"C:\Games\World_of_Tanks_NA",
                @"C:\Games\World_of_Tanks",
                @"C:\Program Files (x86)\World_of_Tanks_NA",
                @"D:\Games\World_of_Tanks_NA"
            }
            : new[]
            {
                @"C:\Games\World_of_Tanks_EU",
                @"C:\Games\World_of_Tanks",
                @"C:\Program Files (x86)\World_of_Tanks_EU",
                @"D:\Games\World_of_Tanks_EU"
            };

        return candidates.FirstOrDefault(IsLikelyGameRoot) ?? candidates[0];
    }

    private static bool IsLikelyGameRoot(string path)
    {
        if (!Directory.Exists(path))
        {
            return false;
        }

        return File.Exists(Path.Combine(path, "WorldOfTanks.exe"))
               || File.Exists(Path.Combine(path, "WorldOfTanksLauncher.exe"))
               || File.Exists(Path.Combine(path, "version.xml"))
               || Directory.Exists(Path.Combine(path, "mods"))
               || Directory.Exists(Path.Combine(path, "res_mods"));
    }

    private static string DetectRegionFromPath(string path)
    {
        var upper = path.ToUpperInvariant();
        if (upper.Contains("_NA") || upper.Contains("WORLD_OF_TANKS_NA"))
        {
            return "NA";
        }

        if (upper.Contains("_EU") || upper.Contains("WORLD_OF_TANKS_EU"))
        {
            return "EU";
        }

        return "Unknown";
    }

    private static string DetectGameVersion(string gameRoot)
    {
        foreach (var candidate in new[] { Path.Combine(gameRoot, "version.xml"), Path.Combine(gameRoot, "game_info.xml") })
        {
            if (!File.Exists(candidate))
            {
                continue;
            }

            try
            {
                var xml = XDocument.Load(candidate);
                var xmlText = xml.ToString();
                var match = Regex.Match(xmlText, @"\b\d+\.\d+\.\d+\.\d+\b");
                if (match.Success)
                {
                    return match.Value;
                }
            }
            catch
            {
                var rawText = File.ReadAllText(candidate);
                var match = Regex.Match(rawText, @"\b\d+\.\d+\.\d+\.\d+\b");
                if (match.Success)
                {
                    return match.Value;
                }
            }
        }

        var modFolders = new[] { Path.Combine(gameRoot, "mods"), Path.Combine(gameRoot, "res_mods") };
        foreach (var folder in modFolders)
        {
            if (!Directory.Exists(folder))
            {
                continue;
            }

            var versionDir = Directory.GetDirectories(folder)
                .Select(Path.GetFileName)
                .FirstOrDefault(name => name is not null && Regex.IsMatch(name, @"^\d+\.\d+\.\d+\.\d+$"));

            if (!string.IsNullOrWhiteSpace(versionDir))
            {
                return versionDir;
            }
        }

        return string.Empty;
    }

    private void ValidateSelectedPath()
    {
        var targetRoot = InstallPathTextBox.Text.Trim();
        var hasSelectedInstallPackages = _packages.Any(x => x.IsSelected && !x.IsMaintenance);
        var hasSelectedMaintenance = _packages.Any(x => x.IsSelected && x.IsMaintenance);

        if (string.IsNullOrWhiteSpace(targetRoot))
        {
            VersionStatusTextBlock.Text = "Escolha a pasta raiz do jogo.";
            VersionStatusTextBlock.Foreground = FindResource("MutedBrush") as System.Windows.Media.Brush;
            InstallButton.IsEnabled = false;
            return;
        }

        if (!Directory.Exists(targetRoot))
        {
            VersionStatusTextBlock.Text = "A pasta escolhida nao existe.";
            VersionStatusTextBlock.Foreground = System.Windows.Media.Brushes.OrangeRed;
            InstallButton.IsEnabled = false;
            return;
        }

        if (!hasSelectedInstallPackages && hasSelectedMaintenance)
        {
            VersionStatusTextBlock.Text = "Apenas manutencao selecionada. A limpeza de cache pode ser executada sem validar a versao do modpack.";
            VersionStatusTextBlock.Foreground = System.Windows.Media.Brushes.LightGreen;
            InstallButton.IsEnabled = !_isInstalling;
            return;
        }

        var detectedVersion = DetectGameVersion(targetRoot);
        if (string.IsNullOrWhiteSpace(detectedVersion))
        {
            VersionStatusTextBlock.Text = $"Nao foi possivel detetar a versao do cliente em {targetRoot}.";
            VersionStatusTextBlock.Foreground = System.Windows.Media.Brushes.Orange;
            InstallButton.IsEnabled = false;
            return;
        }

        if (!string.Equals(detectedVersion, _manifest.GameVersion, StringComparison.Ordinal))
        {
            VersionStatusTextBlock.Text = $"Versao do jogo {detectedVersion}. O modpack exige {_manifest.GameVersion}.";
            VersionStatusTextBlock.Foreground = System.Windows.Media.Brushes.OrangeRed;
            InstallButton.IsEnabled = false;
            return;
        }

        VersionStatusTextBlock.Text = $"Versao validada: {detectedVersion}. O modpack e compativel com este cliente.";
        VersionStatusTextBlock.Foreground = System.Windows.Media.Brushes.LightGreen;
        InstallButton.IsEnabled = !_isInstalling;
    }

    private void BrowseButton_Click(object sender, RoutedEventArgs e)
    {
        using var dialog = new Forms.FolderBrowserDialog
        {
            Description = "Escolha a pasta raiz do World of Tanks",
            UseDescriptionForTitle = true,
            ShowNewFolderButton = false
        };

        if (Directory.Exists(InstallPathTextBox.Text))
        {
            dialog.InitialDirectory = InstallPathTextBox.Text;
        }

        if (dialog.ShowDialog() == Forms.DialogResult.OK)
        {
            InstallPathTextBox.Text = dialog.SelectedPath;
        }
    }

    private void SelectAllButton_Click(object sender, RoutedEventArgs e)
    {
        foreach (var package in _packages)
        {
            package.IsSelected = true;
        }

        UpdateSelectionSummary();
    }

    private void ClearSelectionButton_Click(object sender, RoutedEventArgs e)
    {
        foreach (var package in _packages)
        {
            package.IsSelected = false;
        }

        UpdateSelectionSummary();
    }

    private void UpdateSelectionSummary()
    {
        var selected = _packages.Where(x => x.IsSelected).ToList();
        var totalBytes = selected.Sum(x => x.Package.SizeBytes);
        var maintenanceCount = selected.Count(x => x.IsMaintenance);
        SelectionSummaryText.Text = $"{selected.Count} item(ns) selecionado(s) | {totalBytes / 1024d / 1024d:0.00} MB | {maintenanceCount} manutencao";
    }

    private async void InstallButton_Click(object sender, RoutedEventArgs e)
    {
        if (_isInstalling)
        {
            return;
        }

        var targetRoot = InstallPathTextBox.Text.Trim();
        if (string.IsNullOrWhiteSpace(targetRoot))
        {
            WpfMessageBox.Show("Escolha a pasta raiz do jogo antes de continuar.", "Driftkings Installer", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        if (!Directory.Exists(targetRoot))
        {
            WpfMessageBox.Show("A pasta escolhida nao existe.", "Driftkings Installer", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        if (!IsLikelyGameRoot(targetRoot))
        {
            var result = WpfMessageBox.Show(
                "A pasta escolhida nao parece ser a raiz do World of Tanks. Quer continuar mesmo assim?",
                "Driftkings Installer",
                MessageBoxButton.YesNo,
                MessageBoxImage.Question);

            if (result != MessageBoxResult.Yes)
            {
                return;
            }
        }

        var selected = _packages.Where(x => x.IsSelected).ToList();
        if (selected.Count == 0)
        {
            WpfMessageBox.Show("Selecione pelo menos um pacote.", "Driftkings Installer", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        var selectedInstallPackages = selected.Where(x => !x.IsMaintenance).ToList();
        var selectedMaintenance = selected.Where(x => x.IsMaintenance).ToList();

        var detectedVersion = DetectGameVersion(targetRoot);
        if (selectedInstallPackages.Count > 0 && !string.Equals(detectedVersion, _manifest.GameVersion, StringComparison.Ordinal))
        {
            WpfMessageBox.Show(
                $"A versao do cliente e {detectedVersion} e nao coincide com a versao exigida {_manifest.GameVersion}.",
                "Driftkings Installer",
                MessageBoxButton.OK,
                MessageBoxImage.Warning);
            return;
        }

        _isInstalling = true;
        InstallButton.IsEnabled = false;
        try
        {
            if (selectedMaintenance.Any(x => x.Package.Id == "__clear_cache__"))
            {
                StatusTextBlock.Text = "A limpar cache do cliente...";
                ClearGameCache(_selectedRegion);
            }

            if (selectedInstallPackages.Count > 0)
            {
                await InstallPackagesAsync(selectedInstallPackages, targetRoot);
                StatusTextBlock.Text = $"Instalacao concluida em {targetRoot}";
                InstallProgressBar.Value = 100;
            }
            else
            {
                StatusTextBlock.Text = "Manutencao concluida com sucesso.";
                InstallProgressBar.Value = 100;
            }

            var openFolder = WpfMessageBox.Show(
                "Instalacao concluida com sucesso. Quer abrir a pasta do jogo?",
                "Driftkings Installer",
                MessageBoxButton.YesNo,
                MessageBoxImage.Information);

            if (openFolder == MessageBoxResult.Yes)
            {
                Process.Start(new ProcessStartInfo
                {
                    FileName = targetRoot,
                    UseShellExecute = true
                });
            }
        }
        catch (Exception ex)
        {
            StatusTextBlock.Text = "Falha durante a instalacao.";
            WpfMessageBox.Show($"Erro ao instalar os mods.\n\n{ex.Message}", "Driftkings Installer", MessageBoxButton.OK, MessageBoxImage.Error);
        }
        finally
        {
            _isInstalling = false;
            ValidateSelectedPath();
        }
    }

    private static void ClearGameCache(string selectedRegion)
    {
        var roamingRoot = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);
        var cacheRoots = new List<string> { Path.Combine(roamingRoot, "Wargaming.net", "WorldOfTanks") };
        if (selectedRegion == "EU")
        {
            cacheRoots.Add(Path.Combine(roamingRoot, "Wargaming.net", "WorldOfTanksEU"));
        }
        else if (selectedRegion == "NA")
        {
            cacheRoots.Add(Path.Combine(roamingRoot, "Wargaming.net", "WorldOfTanksNA"));
        }
        else
        {
            cacheRoots.Add(Path.Combine(roamingRoot, "Wargaming.net", "WorldOfTanksEU"));
            cacheRoots.Add(Path.Combine(roamingRoot, "Wargaming.net", "WorldOfTanksNA"));
        }

        var knownCacheDirs = new[]
        {
            "account_caches",
            "battle_results",
            "clan_cache",
            "collections_cache",
            "dossier_cache",
            "game_loading_cache",
            "messenger_cache",
            "offers_cache",
            "playlists_cache",
            "storage_cache",
            "veh_cmp_cache",
            "web_cache",
            "wotlda_cache",
            "wot_anniversary_cache"
        };

        foreach (var basePath in cacheRoots.Where(Directory.Exists))
        {
            foreach (var cacheDir in knownCacheDirs)
            {
                TryDeleteDirectory(Path.Combine(basePath, cacheDir));
            }

            TryDeleteDirectory(Path.Combine(basePath, "profile", "cef_cache"));
        }
    }

    private static void TryDeleteDirectory(string path)
    {
        try
        {
            Directory.Delete(path, true);
        }
        catch
        {
        }
    }

    private async Task InstallPackagesAsync(IReadOnlyList<PackageItem> selectedPackages, string targetRoot)
    {
        InstallProgressBar.Value = 0;
        var tempRoot = Path.Combine(Path.GetTempPath(), "DriftkingsInstaller", Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(tempRoot);

        try
        {
            for (var index = 0; index < selectedPackages.Count; index++)
            {
                var package = selectedPackages[index];
                StatusTextBlock.Text = $"A instalar {package.DisplayName}...";

                var tempZipPath = Path.Combine(tempRoot, package.FileName);
                await using (var output = File.Create(tempZipPath))
                await using (var resource = OpenEmbeddedResource($"archives.{package.FileName}"))
                {
                    await resource.CopyToAsync(output);
                }

                ZipFile.ExtractToDirectory(tempZipPath, targetRoot, true);
                InstallProgressBar.Value = ((index + 1d) / selectedPackages.Count) * 100d;
            }
        }
        finally
        {
            if (Directory.Exists(tempRoot))
            {
                Directory.Delete(tempRoot, true);
            }
        }
    }
}
