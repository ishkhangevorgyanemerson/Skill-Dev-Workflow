---
name: csharp-project-creation
description: Create C# (.csproj) projects and Visual Studio solutions (.sln) that build correctly in VS 2022 and above. Use this skill whenever the user asks to create a new C# project, set up a .NET solution, scaffold a C# class library or console app, create or restructure a .csproj file, fix "project skipped" build issues in Visual Studio, or convert between legacy and SDK-style project formats. Also use when merging multiple C# projects into one, renaming projects/namespaces, or setting up a solution from scratch.
---

# C# Project Creation

This skill ensures that C# projects and Visual Studio solutions are created correctly so they build without issues in VS 2022+. The most common problem — VS silently skipping a project during build — is caused by project format and configuration mismatches that are easy to prevent.

## Core Decision: SDK-style vs Legacy csproj

There are two `.csproj` formats. **Always prefer SDK-style** unless there is a specific reason to use legacy.

### When to use SDK-style (default)
- New projects targeting .NET 5/6/7/8/9+ or .NET Framework 4.6.2+
- VS 2022 and above (which has native SDK-style support)
- Projects being modernized or restructured
- Any project where you have a choice

### When to use legacy format
- The user explicitly requests it
- The project must integrate with a build system that only understands legacy format
- Adding to an existing solution where all other projects are legacy and consistency matters more than modernization

Read `references/sdk-style-csproj.md` for SDK-style templates and guidance.
Read `references/legacy-csproj.md` for legacy format templates and guidance.

## Critical Rules

These rules prevent the "Skipped Rebuild All" problem in VS 2022. They apply to both formats.

### 1. Platform naming: AnyCPU in csproj, Any CPU in sln

MSBuild internally normalizes `Any CPU` (with space) to `AnyCPU` (no space) when passing the platform to the project. The two files use different conventions:

- **In `.csproj`**: Always use `AnyCPU` (no space) in `<Platform>` defaults and `Condition` attributes
- **In `.sln`**: The left side of config mappings uses `Any CPU` (with space), the right side uses `AnyCPU` (no space)

```
# In .sln — left side has space, right side has NO space:
{GUID}.Debug|Any CPU.ActiveCfg = Debug|AnyCPU
{GUID}.Debug|Any CPU.Build.0 = Debug|AnyCPU
```

```xml
<!-- In .csproj — always AnyCPU (no space): -->
<Platform Condition=" '$(Platform)' == '' ">AnyCPU</Platform>
<PropertyGroup Condition=" '$(Configuration)|$(Platform)' == 'Debug|AnyCPU' ">
```

### 2. Build.0 lines are required in .sln

Every project configuration in the `.sln` must have BOTH an `ActiveCfg` line AND a `Build.0` line. The `ActiveCfg` line tells VS which configuration to use; the `Build.0` line tells VS to actually build it. Missing `Build.0` = project is skipped silently.

```
# CORRECT — both lines present:
{GUID}.Debug|Any CPU.ActiveCfg = Debug|AnyCPU
{GUID}.Debug|Any CPU.Build.0 = Debug|AnyCPU

# WRONG — missing Build.0, project will be SKIPPED:
{GUID}.Debug|Any CPU.ActiveCfg = Debug|AnyCPU
```

### 3. Project GUID must match between .sln and .csproj

The GUID in the `.sln` project reference must exactly match `<ProjectGuid>` in the `.csproj` (legacy format) or be consistent (SDK-style, where ProjectGuid is optional but if present must match).

### 4. Project type GUID must be correct

In the `.sln` file, the first GUID in the `Project` line is the project type:
- `{FAE04EC0-301F-11D3-BF4B-00C04F79EFBC}` — C# (legacy format)
- `{9A19103F-16F7-4668-BE54-9A1E7A4F7556}` — C# (SDK-style)

Use the correct type GUID for the format you chose.

### 5. Configuration names must match exactly

The configuration names in `.sln` `GlobalSection(SolutionConfigurationPlatforms)` must exactly match what the `.sln` maps to in `GlobalSection(ProjectConfigurationPlatforms)`, and those mapped values must match the `Condition` attributes in `.csproj`.

### 6. SDK-style projects need NuGet restore before first build

After creating an SDK-style project, always run restore before building:
```
dotnet restore
# or
msbuild /t:Restore
```
VS 2022 does this automatically when opening a solution, but command-line builds require an explicit restore.

## Solution File (.sln) Template

Use this template as a starting point. The blank line at the top and the UTF-8 BOM are part of the VS convention.

```

Microsoft Visual Studio Solution File, Format Version 12.00
# Visual Studio Version 17
VisualStudioVersion = 17.0.0.0
MinimumVisualStudioVersion = 10.0.40219.1
Project("{PROJECT-TYPE-GUID}") = "ProjectName", "ProjectName\ProjectName.csproj", "{PROJECT-GUID}"
EndProject
Global
	GlobalSection(SolutionConfigurationPlatforms) = preSolution
		Debug|Any CPU = Debug|Any CPU
		Release|Any CPU = Release|Any CPU
	EndGlobalSection
	GlobalSection(ProjectConfigurationPlatforms) = postSolution
		{PROJECT-GUID}.Debug|Any CPU.ActiveCfg = Debug|AnyCPU
		{PROJECT-GUID}.Debug|Any CPU.Build.0 = Debug|AnyCPU
		{PROJECT-GUID}.Release|Any CPU.ActiveCfg = Release|AnyCPU
		{PROJECT-GUID}.Release|Any CPU.Build.0 = Release|AnyCPU
	EndGlobalSection
	GlobalSection(SolutionProperties) = preSolution
		HideSolutionNode = FALSE
	EndGlobalSection
EndGlobal
```

Replace:
- `{PROJECT-TYPE-GUID}` — Use `FAE04EC0-301F-11D3-BF4B-00C04F79EFBC` for legacy, `9A19103F-16F7-4668-BE54-9A1E7A4F7556` for SDK-style
- `{PROJECT-GUID}` — Generate a fresh GUID (use `[guid]::NewGuid()` in PowerShell or `uuidgen` on Linux)
- `ProjectName` — The project name

## Post-Creation Checklist

After creating or modifying a project/solution, always verify:

1. **Build from command line first** — `msbuild MySolution.sln /t:Rebuild` or `dotnet build`. This catches real errors without VS caching issues.
2. **If command line works but VS skips** — Delete `.vs/` folder, close VS, reopen. If still skipped, check the 6 rules above.
3. **For SDK-style: confirm restore ran** — Check that `obj/project.assets.json` exists.
4. **Inspect the Output window** — Set Build output verbosity to Detailed (Tools → Options → Projects and Solutions → Build and Run) to see why a project was skipped.

## Multi-Project Solutions

When adding multiple projects to a solution:
- Each project needs its own unique GUID
- Each project needs its own set of `ActiveCfg` + `Build.0` lines for every solution configuration
- Use solution folders (virtual folders in .sln) for organization if needed

## Renaming Projects or Folders

When renaming a project folder, namespace, or assembly name:

1. **Close VS first** — VS locks files and caches paths
2. Rename files/folders
3. Update all references in `.csproj` and `.sln`
4. **Delete `.vs/` folder** — Contains stale cached paths
5. **Delete `bin/` and `obj/`** — Contain stale build artifacts
6. Reopen VS and verify build
