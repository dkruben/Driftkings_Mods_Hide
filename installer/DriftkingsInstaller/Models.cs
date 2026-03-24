using System.ComponentModel;
using System.Runtime.CompilerServices;
using System.Text.Json.Serialization;

namespace DriftkingsInstaller;

public sealed class InstallerManifest
{
    [JsonPropertyName("title")]
    public string Title { get; set; } = string.Empty;

    [JsonPropertyName("gameVersion")]
    public string GameVersion { get; set; } = string.Empty;

    [JsonPropertyName("packageVersion")]
    public string PackageVersion { get; set; } = string.Empty;

    [JsonPropertyName("packages")]
    public List<InstallerPackage> Packages { get; set; } = new();
}

public sealed class GameInstallation
{
    public string RootPath { get; set; } = string.Empty;

    public string Region { get; set; } = "Unknown";

    public string DetectedVersion { get; set; } = string.Empty;

    public bool VersionMatches { get; set; }

    public string Source { get; set; } = string.Empty;

    public string DisplayLabel =>
        string.IsNullOrWhiteSpace(DetectedVersion)
            ? $"{Region} - {RootPath}"
            : $"{Region} - {RootPath} - v{DetectedVersion}";
}

public sealed class InstallerPackage
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;

    [JsonPropertyName("displayName")]
    public string DisplayName { get; set; } = string.Empty;

    [JsonPropertyName("fileName")]
    public string FileName { get; set; } = string.Empty;

    [JsonPropertyName("description")]
    public string Description { get; set; } = string.Empty;

    [JsonPropertyName("sizeBytes")]
    public long SizeBytes { get; set; }

    [JsonPropertyName("recommended")]
    public bool Recommended { get; set; } = true;

    [JsonPropertyName("isMaintenance")]
    public bool IsMaintenance { get; set; }
}

public sealed class PackageItem : INotifyPropertyChanged
{
    private bool _isSelected;

    public PackageItem(InstallerPackage package)
    {
        Package = package;
        _isSelected = package.Recommended;
    }

    public InstallerPackage Package { get; }

    public string DisplayName => Package.DisplayName;

    public string FileName => Package.FileName;

    public string Subtitle => string.IsNullOrWhiteSpace(Package.Description) ? Package.FileName : Package.Description;

    public bool IsMaintenance => Package.IsMaintenance;

    public string SizeLabel => Package.IsMaintenance ? "Maintenance" : $"{Package.SizeBytes / 1024d / 1024d:0.00} MB";

    public bool IsSelected
    {
        get => _isSelected;
        set
        {
            if (_isSelected == value)
            {
                return;
            }

            _isSelected = value;
            OnPropertyChanged();
        }
    }

    public event PropertyChangedEventHandler? PropertyChanged;

    private void OnPropertyChanged([CallerMemberName] string? propertyName = null)
    {
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
    }
}
