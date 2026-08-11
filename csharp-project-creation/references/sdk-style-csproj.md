# SDK-Style .csproj Reference

SDK-style is the modern project format introduced with .NET Core and fully supported by VS 2022+. It is simpler, auto-globs source files, and eliminates most of the boilerplate of the legacy format.

## Key Characteristics

- Uses `<Project Sdk="Microsoft.NET.Sdk">` root element
- Auto-includes all `.cs` files — no `<Compile Include="...">` entries needed
- Requires NuGet restore (`dotnet restore` or `msbuild /t:Restore`) before first build
- Output goes to `bin\{Config}\{TargetFramework}\` (e.g., `bin\Release\net462\`)
- Project type GUID in `.sln`: `{9A19103F-16F7-4668-BE54-9A1E7A4F7556}`

## Templates

### Class Library — .NET Framework 4.6.2

```xml
<Project Sdk="Microsoft.NET.Sdk">

  <PropertyGroup>
    <TargetFramework>net462</TargetFramework>
    <RootNamespace>MyNamespace</RootNamespace>
    <AssemblyName>MyAssembly</AssemblyName>
    <GenerateAssemblyInfo>false</GenerateAssemblyInfo>
  </PropertyGroup>

  <!-- Framework references not auto-included by the SDK -->
  <ItemGroup>
    <Reference Include="System.Windows.Forms" />
    <Reference Include="System.Drawing" />
    <Reference Include="System.Runtime.Serialization" />
  </ItemGroup>

  <!-- External DLL references -->
  <ItemGroup>
    <Reference Include="SomeExternalLib">
      <HintPath>path\to\SomeExternalLib.dll</HintPath>
      <Private>False</Private>
    </Reference>
  </ItemGroup>

  <!-- WinForms designer metadata (only if using WinForms) -->
  <ItemGroup>
    <Compile Update="MyForm.cs">
      <SubType>Form</SubType>
    </Compile>
    <Compile Update="MyForm.Designer.cs">
      <DependentUpon>MyForm.cs</DependentUpon>
    </Compile>
  </ItemGroup>

</Project>
```

### Class Library — .NET 8

```xml
<Project Sdk="Microsoft.NET.Sdk">

  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <RootNamespace>MyNamespace</RootNamespace>
    <AssemblyName>MyAssembly</AssemblyName>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
  </PropertyGroup>

</Project>
```

### Console App — .NET 8

```xml
<Project Sdk="Microsoft.NET.Sdk">

  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net8.0</TargetFramework>
    <RootNamespace>MyNamespace</RootNamespace>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
  </PropertyGroup>

</Project>
```

### WinForms App — .NET 8

```xml
<Project Sdk="Microsoft.NET.Sdk">

  <PropertyGroup>
    <OutputType>WinExe</OutputType>
    <TargetFramework>net8.0-windows</TargetFramework>
    <UseWindowsForms>true</UseWindowsForms>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
  </PropertyGroup>

</Project>
```

Note: `UseWindowsForms` is only valid for .NET Core 3.0+ / .NET 5+. For .NET Framework targets, add explicit `<Reference>` elements for `System.Windows.Forms` and `System.Drawing` instead.

## Common Properties

| Property | Purpose | Notes |
|---|---|---|
| `TargetFramework` | Target framework moniker | `net462`, `net8.0`, `net8.0-windows`, etc. |
| `RootNamespace` | Default namespace for new files | Defaults to assembly name if omitted |
| `AssemblyName` | Output DLL/EXE name | Defaults to project folder name if omitted |
| `GenerateAssemblyInfo` | Auto-generate AssemblyInfo attributes | Set to `false` if you have a manual `Properties\AssemblyInfo.cs` |
| `OutputType` | `Library` (default), `Exe`, `WinExe` | Omit for class libraries |
| `ImplicitUsings` | Auto-include common `using` statements | .NET 6+ only |
| `Nullable` | Enable nullable reference types | .NET 6+ recommended |

## Auto-Globbing Behavior

SDK-style projects automatically include:
- All `*.cs` files recursively
- All files in `Content`, `EmbeddedResource`, etc.

To **exclude** files:
```xml
<ItemGroup>
  <Compile Remove="Legacy\**" />
</ItemGroup>
```

To **override metadata** on auto-included files (e.g., WinForms designer):
```xml
<ItemGroup>
  <Compile Update="MyForm.cs">
    <SubType>Form</SubType>
  </Compile>
</ItemGroup>
```

Note: Use `Update` (not `Include`) when modifying metadata on auto-globbed files. Using `Include` on an already-included file causes a duplicate compile error.

## .NET Framework Targeting

SDK-style csproj works with .NET Framework 4.6.2+ but has these differences from .NET Core/.NET 5+:

- You must have the targeting pack installed (e.g., `.NET Framework 4.6.2 Developer Pack`)
- `UseWindowsForms` and `UseWPF` are NOT available — use explicit `<Reference>` elements instead
- `ImplicitUsings` is NOT available
- `System`, `System.Core`, `System.Xml`, `System.Data` are auto-referenced; specialty assemblies like `System.Windows.Forms`, `System.Drawing`, `System.Runtime.Serialization` need explicit `<Reference>` entries
- Output path includes framework folder: `bin\Release\net462\`

## NuGet Package References

```xml
<ItemGroup>
  <PackageReference Include="Newtonsoft.Json" Version="13.0.3" />
  <PackageReference Include="NLog" Version="5.2.8" />
</ItemGroup>
```
