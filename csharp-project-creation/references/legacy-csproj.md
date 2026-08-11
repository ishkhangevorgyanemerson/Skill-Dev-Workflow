# Legacy .csproj Reference

Legacy (non-SDK) format is the older project format used by .NET Framework projects prior to .NET Core. VS 2022 still supports it, but it requires more boilerplate and explicit file listings.

## Key Characteristics

- Uses `<Project ToolsVersion="..." DefaultTargets="Build" xmlns="...">` root element
- Every source file must be explicitly listed with `<Compile Include="...">`
- No NuGet restore needed (unless using PackageReference — rare in legacy)
- Output goes to `bin\{Config}\` (e.g., `bin\Release\`)
- Project type GUID in `.sln`: `{FAE04EC0-301F-11D3-BF4B-00C04F79EFBC}`

## Template: Class Library — .NET Framework 4.6.2

```xml
<?xml version="1.0" encoding="utf-8"?>
<Project ToolsVersion="Current" DefaultTargets="Build" xmlns="http://schemas.microsoft.com/developer/msbuild/2003">
  <Import Project="$(MSBuildExtensionsPath)\$(MSBuildToolsVersion)\Microsoft.Common.props" Condition="Exists('$(MSBuildExtensionsPath)\$(MSBuildToolsVersion)\Microsoft.Common.props')" />
  <PropertyGroup>
    <Configuration Condition=" '$(Configuration)' == '' ">Debug</Configuration>
    <Platform Condition=" '$(Platform)' == '' ">AnyCPU</Platform>
    <ProjectGuid>{YOUR-GUID-HERE}</ProjectGuid>
    <OutputType>Library</OutputType>
    <AppDesignerFolder>Properties</AppDesignerFolder>
    <RootNamespace>MyNamespace</RootNamespace>
    <AssemblyName>MyAssembly</AssemblyName>
    <TargetFrameworkVersion>v4.6.2</TargetFrameworkVersion>
    <FileAlignment>512</FileAlignment>
    <TargetFrameworkProfile />
  </PropertyGroup>
  <PropertyGroup Condition=" '$(Configuration)|$(Platform)' == 'Debug|AnyCPU' ">
    <DebugSymbols>true</DebugSymbols>
    <DebugType>full</DebugType>
    <Optimize>false</Optimize>
    <OutputPath>bin\Debug\</OutputPath>
    <DefineConstants>DEBUG;TRACE</DefineConstants>
    <ErrorReport>prompt</ErrorReport>
    <WarningLevel>4</WarningLevel>
  </PropertyGroup>
  <PropertyGroup Condition=" '$(Configuration)|$(Platform)' == 'Release|AnyCPU' ">
    <DebugType>pdbonly</DebugType>
    <Optimize>true</Optimize>
    <OutputPath>bin\Release\</OutputPath>
    <DefineConstants>TRACE</DefineConstants>
    <ErrorReport>prompt</ErrorReport>
    <WarningLevel>4</WarningLevel>
  </PropertyGroup>
  <ItemGroup>
    <Reference Include="System" />
    <Reference Include="System.Core" />
    <Reference Include="System.Xml" />
    <!-- Add other framework references as needed -->
  </ItemGroup>
  <ItemGroup>
    <Compile Include="MyClass.cs" />
    <Compile Include="Properties\AssemblyInfo.cs" />
  </ItemGroup>
  <Import Project="$(MSBuildToolsPath)\Microsoft.CSharp.targets" />
</Project>
```

## Critical: ToolsVersion

Use `ToolsVersion="Current"` for VS 2022 compatibility. Older values like `"4.0"`, `"14.0"`, `"15.0"` may cause VS 2022 to skip the project silently if the corresponding toolset is not installed.

| Value | Meaning | VS 2022 Support |
|---|---|---|
| `"Current"` | Use whatever MSBuild is available | Always works |
| `"4.0"` | .NET 4.0 era toolset | May cause skip |
| `"14.0"` | VS 2015 toolset | May cause skip |
| `"15.0"` | VS 2017 toolset | May cause skip |

## Platform Convention

In legacy csproj, always use `AnyCPU` (no space) everywhere:
- `<Platform>` default value
- `Condition` attributes on `<PropertyGroup>`

The `.sln` file handles the `Any CPU` ↔ `AnyCPU` mapping.

## Explicit File Listing

Every `.cs` file must be listed. When adding, removing, or renaming files, update the csproj:

```xml
<ItemGroup>
  <Compile Include="MyClass.cs" />
  <Compile Include="SubFolder\Helper.cs" />
  <Compile Include="MyForm.cs">
    <SubType>Form</SubType>
  </Compile>
  <Compile Include="MyForm.Designer.cs">
    <DependentUpon>MyForm.cs</DependentUpon>
  </Compile>
  <Compile Include="Properties\AssemblyInfo.cs" />
</ItemGroup>
```

Forgetting to update a `<Compile Include>` entry after renaming a file is a common source of build errors.

## When to Convert to SDK-Style

Consider converting legacy to SDK-style when:
- The project targets .NET Framework 4.6.2 or later
- You're restructuring or merging projects
- VS 2022 is the minimum supported IDE
- The project has no complex MSBuild customizations that depend on legacy import order

The conversion is straightforward:
1. Replace the entire csproj content with the SDK-style template
2. Remove all `<Compile Include>` entries (auto-globbing handles it)
3. Keep only non-standard references (external DLLs, NuGet packages)
4. Add `<GenerateAssemblyInfo>false</GenerateAssemblyInfo>` if you have a manual AssemblyInfo.cs
5. Run `dotnet restore` or `msbuild /t:Restore`
6. Delete `bin/`, `obj/`, `.vs/` and rebuild
