if __name__ == "__main__":
    # WingetUI cannot be run directly from this file, it must be run by importing the wingetui module
    import os
    import subprocess
    import sys
    sys.exit(subprocess.run(["cmd", "/C", "python", "-m", "wingetui"], shell=True, cwd=os.path.dirname(__file__).split("wingetui")[0]).returncode)

import os
import subprocess

from wingetui.Core.Tools import *
from wingetui.Core.Tools import _
from wingetui.PackageEngine.Classes import *


class WingetPackageManager(PackageManagerWithSources):

    IS_ARM = False
    try:
        if subprocess.check_output("cmd.exe /C echo %PROCESSOR_ARCHITECTURE%") == b'ARM64\r\n':
            IS_ARM = True
    except Exception as e:
        report(e)

    if getSettings("UseSystemWinget"):
        EXECUTABLE = "winget.exe"
    else:
        if getSettings("EnableArmWinget") or IS_ARM:
            print("🟠 USING ARM BUILT-In WINGET")
            IS_ARM = True
            EXECUTABLE = os.path.join(realpath, "PackageEngine/Managers", "winget-cli_arm64", "winget.exe")
        else:
            EXECUTABLE = os.path.join(realpath, "PackageEngine/Managers", "winget-cli_x64", "winget.exe")

    NAME = "Winget"

    wingetIcon = None
    localIcon = None
    steamIcon = None
    gogIcon = None
    uPlayIcon = None
    msStoreIcon = None
    wsaIcon = None

    def __init__(self):
        super().__init__()
        self.Capabilities.CanRunAsAdmin = True
        self.Capabilities.CanSkipIntegrityChecks = True
        self.Capabilities.CanRunInteractively = True
        self.Capabilities.SupportsCustomVersions = True
        self.Capabilities.SupportsCustomArchitectures = True
        self.Capabilities.SupportsCustomScopes = True
        self.Capabilities.SupportsCustomLocations = True
        self.Capabilities.SupportsCustomSources = True
        self.Capabilities.Sources.KnowsPackageCount = False
        self.Capabilities.Sources.KnowsUpdateDate = False

        self.Properties.Name = self.NAME
        self.Properties.Description = _("Microsoft's official package manager. Full of well-known and verified packages<br>Contains: <b>General Software, Microsoft Store apps</b>")
        self.Properties.Icon = getMedia("winget")
        self.Properties.ColorIcon = getMedia("winget_color")
        self.IconPath = self.Properties.Icon

        self.Properties.InstallVerb = "install"
        self.Properties.UpdateVerb = "update"
        self.Properties.UninstallVerb = "uninstall"
        self.Properties.ExecutableName = "winget"

        self.BLACKLISTED_PACKAGE_IDS = ["", "have", "the", "Id"]
        self.BLACKLISTED_PACKAGE_VERSIONS = ["have", "an", "'winget", "pin'", "have", "an", "Version"]

        self.KnownSources = [
            ManagerSource(self, "winget", "https://cdn.winget.microsoft.com/cache"),
            ManagerSource(self, "msstore", "https://storeedgefd.dsx.mp.microsoft.com/v9.0"),
        ]

    def isEnabled(self) -> bool:
        return not getSettings(f"Disable{self.NAME}")
    
    def convertWingetReturnCode(self, returncode: int) -> str:
        # https://github.com/microsoft/winget-cli/blob/master/doc/windows/package-manager/winget/returnCodes.md
        # Source 27.01.2024 https://github.com/microsoft/winget-cli/blob/master/src/AppInstallerSharedLib/Public/AppInstallerErrors.h
        dict = {
            0x8A150001 :"APPINSTALLER_CLI_ERROR_INTERNAL_ERROR", 
            0x8A150002 :"APPINSTALLER_CLI_ERROR_INVALID_CL_ARGUMENTS", 
            0x8A150003 :"APPINSTALLER_CLI_ERROR_COMMAND_FAILED", 
            0x8A150004 :"APPINSTALLER_CLI_ERROR_MANIFEST_FAILED", 
            0x8A150005 :"APPINSTALLER_CLI_ERROR_CTRL_SIGNAL_RECEIVED", 
            0x8A150006 :"APPINSTALLER_CLI_ERROR_SHELLEXEC_INSTALL_FAILED", 
            0x8A150007 :"APPINSTALLER_CLI_ERROR_UNSUPPORTED_MANIFESTVERSION", 
            0x8A150008 :"APPINSTALLER_CLI_ERROR_DOWNLOAD_FAILED", 
            0x8A150009 :"APPINSTALLER_CLI_ERROR_CANNOT_WRITE_TO_UPLEVEL_INDEX", 
            0x8A15000A :"APPINSTALLER_CLI_ERROR_INDEX_INTEGRITY_COMPROMISED", 
            0x8A15000B :"APPINSTALLER_CLI_ERROR_SOURCES_INVALID", 
            0x8A15000C :"APPINSTALLER_CLI_ERROR_SOURCE_NAME_ALREADY_EXISTS", 
            0x8A15000D :"APPINSTALLER_CLI_ERROR_INVALID_SOURCE_TYPE", 
            0x8A15000E :"APPINSTALLER_CLI_ERROR_PACKAGE_IS_BUNDLE", 
            0x8A15000F :"APPINSTALLER_CLI_ERROR_SOURCE_DATA_MISSING", 
            0x8A150010 :"APPINSTALLER_CLI_ERROR_NO_APPLICABLE_INSTALLER", 
            0x8A150011 :"APPINSTALLER_CLI_ERROR_INSTALLER_HASH_MISMATCH", 
            0x8A150012 :"APPINSTALLER_CLI_ERROR_SOURCE_NAME_DOES_NOT_EXIST", 
            0x8A150013 :"APPINSTALLER_CLI_ERROR_SOURCE_ARG_ALREADY_EXISTS", 
            0x8A150014 :"APPINSTALLER_CLI_ERROR_NO_APPLICATIONS_FOUND", 
            0x8A150015 :"APPINSTALLER_CLI_ERROR_NO_SOURCES_DEFINED", 
            0x8A150016 :"APPINSTALLER_CLI_ERROR_MULTIPLE_APPLICATIONS_FOUND", 
            0x8A150017 :"APPINSTALLER_CLI_ERROR_NO_MANIFEST_FOUND", 
            0x8A150018 :"APPINSTALLER_CLI_ERROR_EXTENSION_PUBLIC_FAILED", 
            0x8A150019 :"APPINSTALLER_CLI_ERROR_COMMAND_REQUIRES_ADMIN", 
            0x8A15001A :"APPINSTALLER_CLI_ERROR_SOURCE_NOT_SECURE", 
            0x8A15001B :"APPINSTALLER_CLI_ERROR_MSSTORE_BLOCKED_BY_POLICY", 
            0x8A15001C :"APPINSTALLER_CLI_ERROR_MSSTORE_APP_BLOCKED_BY_POLICY", 
            0x8A15001D :"APPINSTALLER_CLI_ERROR_EXPERIMENTAL_FEATURE_DISABLED", 
            0x8A15001E :"APPINSTALLER_CLI_ERROR_MSSTORE_INSTALL_FAILED", 
            0x8A15001F :"APPINSTALLER_CLI_ERROR_COMPLETE_INPUT_BAD", 
            0x8A150020 :"APPINSTALLER_CLI_ERROR_YAML_INIT_FAILED", 
            0x8A150021 :"APPINSTALLER_CLI_ERROR_YAML_INVALID_MAPPING_KEY", 
            0x8A150022 :"APPINSTALLER_CLI_ERROR_YAML_DUPLICATE_MAPPING_KEY", 
            0x8A150023 :"APPINSTALLER_CLI_ERROR_YAML_INVALID_OPERATION", 
            0x8A150024 :"APPINSTALLER_CLI_ERROR_YAML_DOC_BUILD_FAILED", 
            0x8A150025 :"APPINSTALLER_CLI_ERROR_YAML_INVALID_EMITTER_STATE", 
            0x8A150026 :"APPINSTALLER_CLI_ERROR_YAML_INVALID_DATA", 
            0x8A150027 :"APPINSTALLER_CLI_ERROR_LIBYAML_ERROR", 
            0x8A150028 :"APPINSTALLER_CLI_ERROR_MANIFEST_VALIDATION_WARNING", 
            0x8A150029 :"APPINSTALLER_CLI_ERROR_MANIFEST_VALIDATION_FAILURE", 
            0x8A15002A :"APPINSTALLER_CLI_ERROR_INVALID_MANIFEST", 
            0x8A15002B :"APPINSTALLER_CLI_ERROR_UPDATE_NOT_APPLICABLE", 
            0x8A15002C :"APPINSTALLER_CLI_ERROR_UPDATE_ALL_HAS_FAILURE", 
            0x8A15002D :"APPINSTALLER_CLI_ERROR_INSTALLER_SECURITY_CHECK_FAILED", 
            0x8A15002E :"APPINSTALLER_CLI_ERROR_DOWNLOAD_SIZE_MISMATCH", 
            0x8A15002F :"APPINSTALLER_CLI_ERROR_NO_UNINSTALL_INFO_FOUND", 
            0x8A150030 :"APPINSTALLER_CLI_ERROR_EXEC_UNINSTALL_COMMAND_FAILED", 
            0x8A150031 :"APPINSTALLER_CLI_ERROR_ICU_BREAK_ITERATOR_ERROR", 
            0x8A150032 :"APPINSTALLER_CLI_ERROR_ICU_CASEMAP_ERROR", 
            0x8A150033 :"APPINSTALLER_CLI_ERROR_ICU_REGEX_ERROR", 
            0x8A150034 :"APPINSTALLER_CLI_ERROR_IMPORT_INSTALL_FAILED", 
            0x8A150035 :"APPINSTALLER_CLI_ERROR_NOT_ALL_PACKAGES_FOUND", 
            0x8A150036 :"APPINSTALLER_CLI_ERROR_JSON_INVALID_FILE", 
            0x8A150037 :"APPINSTALLER_CLI_ERROR_SOURCE_NOT_REMOTE", 
            0x8A150038 :"APPINSTALLER_CLI_ERROR_UNSUPPORTED_RESTSOURCE", 
            0x8A150039 :"APPINSTALLER_CLI_ERROR_RESTSOURCE_INVALID_DATA", 
            0x8A15003A :"APPINSTALLER_CLI_ERROR_BLOCKED_BY_POLICY", 
            0x8A15003B :"APPINSTALLER_CLI_ERROR_RESTSOURCE_INTERNAL_ERROR", 
            0x8A15003C :"APPINSTALLER_CLI_ERROR_RESTSOURCE_INVALID_URL", 
            0x8A15003D :"APPINSTALLER_CLI_ERROR_RESTSOURCE_UNSUPPORTED_MIME_TYPE", 
            0x8A15003E :"APPINSTALLER_CLI_ERROR_RESTSOURCE_INVALID_VERSION", 
            0x8A15003F :"APPINSTALLER_CLI_ERROR_SOURCE_DATA_INTEGRITY_FAILURE", 
            0x8A150040 :"APPINSTALLER_CLI_ERROR_STREAM_READ_FAILURE", 
            0x8A150041 :"APPINSTALLER_CLI_ERROR_PACKAGE_AGREEMENTS_NOT_ACCEPTED", 
            0x8A150042 :"APPINSTALLER_CLI_ERROR_PROMPT_INPUT_ERROR", 
            0x8A150043 :"APPINSTALLER_CLI_ERROR_UNSUPPORTED_SOURCE_REQUEST", 
            0x8A150044 :"APPINSTALLER_CLI_ERROR_RESTSOURCE_ENDPOINT_NOT_FOUND", 
            0x8A150045 :"APPINSTALLER_CLI_ERROR_SOURCE_OPEN_FAILED", 
            0x8A150046 :"APPINSTALLER_CLI_ERROR_SOURCE_AGREEMENTS_NOT_ACCEPTED", 
            0x8A150047 :"APPINSTALLER_CLI_ERROR_CUSTOMHEADER_EXCEEDS_MAXLENGTH", 
            0x8A150048 :"APPINSTALLER_CLI_ERROR_MISSING_RESOURCE_FILE", 
            0x8A150049 :"APPINSTALLER_CLI_ERROR_MSI_INSTALL_FAILED", 
            0x8A15004A :"APPINSTALLER_CLI_ERROR_INVALID_MSIEXEC_ARGUMENT", 
            0x8A15004B :"APPINSTALLER_CLI_ERROR_FAILED_TO_OPEN_ALL_SOURCES", 
            0x8A15004C :"APPINSTALLER_CLI_ERROR_DEPENDENCIES_VALIDATION_FAILED", 
            0x8A15004D :"APPINSTALLER_CLI_ERROR_MISSING_PACKAGE", 
            0x8A15004E :"APPINSTALLER_CLI_ERROR_INVALID_TABLE_COLUMN", 
            0x8A15004F :"APPINSTALLER_CLI_ERROR_UPGRADE_VERSION_NOT_NEWER", 
            0x8A150050 :"APPINSTALLER_CLI_ERROR_UPGRADE_VERSION_UNKNOWN", 
            0x8A150051 :"APPINSTALLER_CLI_ERROR_ICU_CONVERSION_ERROR", 
            0x8A150052 :"APPINSTALLER_CLI_ERROR_PORTABLE_INSTALL_FAILED", 
            0x8A150053 :"APPINSTALLER_CLI_ERROR_PORTABLE_REPARSE_POINT_NOT_SUPPORTED", 
            0x8A150054 :"APPINSTALLER_CLI_ERROR_PORTABLE_PACKAGE_ALREADY_EXISTS", 
            0x8A150055 :"APPINSTALLER_CLI_ERROR_PORTABLE_SYMLINK_PATH_IS_DIRECTORY", 
            0x8A150056 :"APPINSTALLER_CLI_ERROR_INSTALLER_PROHIBITS_ELEVATION", 
            0x8A150057 :"APPINSTALLER_CLI_ERROR_PORTABLE_UNINSTALL_FAILED", 
            0x8A150058 :"APPINSTALLER_CLI_ERROR_ARP_VERSION_VALIDATION_FAILED", 
            0x8A150059 :"APPINSTALLER_CLI_ERROR_UNSUPPORTED_ARGUMENT", 
            0x8A15005A :"APPINSTALLER_CLI_ERROR_BIND_WITH_EMBEDDED_NULL", 
            0x8A15005B :"APPINSTALLER_CLI_ERROR_NESTEDINSTALLER_NOT_FOUND", 
            0x8A15005C :"APPINSTALLER_CLI_ERROR_EXTRACT_ARCHIVE_FAILED", 
            0x8A15005D :"APPINSTALLER_CLI_ERROR_NESTEDINSTALLER_INVALID_PATH", 
            0x8A15005E :"APPINSTALLER_CLI_ERROR_PINNED_CERTIFICATE_MISMATCH", 
            0x8A15005F :"APPINSTALLER_CLI_ERROR_INSTALL_LOCATION_REQUIRED", 
            0x8A150060 :"APPINSTALLER_CLI_ERROR_ARCHIVE_SCAN_FAILED", 
            0x8A150061 :"APPINSTALLER_CLI_ERROR_PACKAGE_ALREADY_INSTALLED", 
            0x8A150062 :"APPINSTALLER_CLI_ERROR_PIN_ALREADY_EXISTS", 
            0x8A150063 :"APPINSTALLER_CLI_ERROR_PIN_DOES_NOT_EXIST", 
            0x8A150064 :"APPINSTALLER_CLI_ERROR_CANNOT_OPEN_PINNING_INDEX", 
            0x8A150065 :"APPINSTALLER_CLI_ERROR_MULTIPLE_INSTALL_FAILED", 
            0x8A150066 :"APPINSTALLER_CLI_ERROR_MULTIPLE_UNINSTALL_FAILED", 
            0x8A150067 :"APPINSTALLER_CLI_ERROR_NOT_ALL_QUERIES_FOUND_SINGLE", 
            0x8A150068 :"APPINSTALLER_CLI_ERROR_PACKAGE_IS_PINNED", 
            0x8A150069 :"APPINSTALLER_CLI_ERROR_PACKAGE_IS_STUB", 
            0x8A15006A :"APPINSTALLER_CLI_ERROR_APPTERMINATION_RECEIVED", 
            0x8A15006B :"APPINSTALLER_CLI_ERROR_DOWNLOAD_DEPENDENCIES", 
            0x8A15006C :"APPINSTALLER_CLI_ERROR_DOWNLOAD_COMMAND_PROHIBITED", 
            0x8A15006D :"APPINSTALLER_CLI_ERROR_SERVICE_UNAVAILABLE", 
            0x8A15006E :"APPINSTALLER_CLI_ERROR_RESUME_ID_NOT_FOUND", 
            0x8A15006F :"APPINSTALLER_CLI_ERROR_CLIENT_VERSION_MISMATCH", 
            0x8A150070 :"APPINSTALLER_CLI_ERROR_INVALID_RESUME_STATE", 
            0x8A150071 :"APPINSTALLER_CLI_ERROR_CANNOT_OPEN_CHECKPOINT_INDEX", 
            0x8A150072 :"APPINSTALLER_CLI_ERROR_RESUME_LIMIT_EXCEEDED", 
            # Install errors
            0x8A150101 :"APPINSTALLER_CLI_ERROR_INSTALL_PACKAGE_IN_USE", 
            0x8A150102 :"APPINSTALLER_CLI_ERROR_INSTALL_INSTALL_IN_PROGRESS", 
            0x8A150103 :"APPINSTALLER_CLI_ERROR_INSTALL_FILE_IN_USE", 
            0x8A150104 :"APPINSTALLER_CLI_ERROR_INSTALL_MISSING_DEPENDENCY", 
            0x8A150105 :"APPINSTALLER_CLI_ERROR_INSTALL_DISK_FULL", 
            0x8A150106 :"APPINSTALLER_CLI_ERROR_INSTALL_INSUFFICIENT_MEMORY", 
            0x8A150107 :"APPINSTALLER_CLI_ERROR_INSTALL_NO_NETWORK", 
            0x8A150108 :"APPINSTALLER_CLI_ERROR_INSTALL_CONTACT_SUPPORT", 
            0x8A150109 :"APPINSTALLER_CLI_ERROR_INSTALL_REBOOT_REQUIRED_TO_FINISH", 
            0x8A15010A :"APPINSTALLER_CLI_ERROR_INSTALL_REBOOT_REQUIRED_FOR_INSTALL", 
            0x8A15010B :"APPINSTALLER_CLI_ERROR_INSTALL_REBOOT_INITIATED", 
            0x8A15010C :"APPINSTALLER_CLI_ERROR_INSTALL_CANCELLED_BY_USER", 
            0x8A15010D :"APPINSTALLER_CLI_ERROR_INSTALL_ALREADY_INSTALLED", 
            0x8A15010E :"APPINSTALLER_CLI_ERROR_INSTALL_DOWNGRADE", 
            0x8A15010F :"APPINSTALLER_CLI_ERROR_INSTALL_BLOCKED_BY_POLICY", 
            0x8A150110 :"APPINSTALLER_CLI_ERROR_INSTALL_DEPENDENCIES", 
            0x8A150111 :"APPINSTALLER_CLI_ERROR_INSTALL_PACKAGE_IN_USE_BY_APPLICATION", 
            0x8A150112 :"APPINSTALLER_CLI_ERROR_INSTALL_INVALID_PARAMETER", 
            0x8A150113 :"APPINSTALLER_CLI_ERROR_INSTALL_SYSTEM_NOT_SUPPORTED", 
            0x8A150114 :"APPINSTALLER_CLI_ERROR_INSTALL_UPGRADE_NOT_SUPPORTED", 

            # Status values for check package installed status results.
            # Partial success has the success bit(first bit  set to 0.
            # TODO S_OK :"WINGET_INSTALLED_STATUS_ARP_ENTRY_FOUND",
            0x8A150201 :"WINGET_INSTALLED_STATUS_ARP_ENTRY_NOT_FOUND", 
            # TODO S_OK :"WINGET_INSTALLED_STATUS_INSTALL_LOCATION_FOUND",
            0x0A150202 :"WINGET_INSTALLED_STATUS_INSTALL_LOCATION_NOT_APPLICABLE", 
            0x8A150203 :"WINGET_INSTALLED_STATUS_INSTALL_LOCATION_NOT_FOUND", 
            # TODO S_OK :"WINGET_INSTALLED_STATUS_FILE_HASH_MATCH",
            0x8A150204 :"WINGET_INSTALLED_STATUS_FILE_HASH_MISMATCH", 
            0x8A150205 :"WINGET_INSTALLED_STATUS_FILE_NOT_FOUND", 
            0x0A150206 :"WINGET_INSTALLED_STATUS_FILE_FOUND_WITHOUT_HASH_CHECK", 
            0x8A150207 :"WINGET_INSTALLED_STATUS_FILE_ACCESS_ERROR", 

            # Configuration Errors
            0x8A15C001 :"WINGET_CONFIG_ERROR_INVALID_CONFIGURATION_FILE", 
            0x8A15C002 :"WINGET_CONFIG_ERROR_INVALID_YAML", 
            0x8A15C003 :"WINGET_CONFIG_ERROR_INVALID_FIELD_TYPE", 
            0x8A15C004 :"WINGET_CONFIG_ERROR_UNKNOWN_CONFIGURATION_FILE_VERSION", 
            0x8A15C005 :"WINGET_CONFIG_ERROR_SET_APPLY_FAILED", 
            0x8A15C006 :"WINGET_CONFIG_ERROR_DUPLICATE_IDENTIFIER", 
            0x8A15C007 :"WINGET_CONFIG_ERROR_MISSING_DEPENDENCY", 
            0x8A15C008 :"WINGET_CONFIG_ERROR_DEPENDENCY_UNSATISFIED", 
            0x8A15C009 :"WINGET_CONFIG_ERROR_ASSERTION_FAILED", 
            0x8A15C00A :"WINGET_CONFIG_ERROR_MANUALLY_SKIPPED", 
            0x8A15C00B :"WINGET_CONFIG_ERROR_WARNING_NOT_ACCEPTED", 
            0x8A15C00C :"WINGET_CONFIG_ERROR_SET_DEPENDENCY_CYCLE", 
            0x8A15C00D :"WINGET_CONFIG_ERROR_INVALID_FIELD_VALUE", 
            0x8A15C00E :"WINGET_CONFIG_ERROR_MISSING_FIELD", 
            0x8A15C00F :"WINGET_CONFIG_ERROR_TEST_FAILED", 
            0x8A15C010 :"WINGET_CONFIG_ERROR_TEST_NOT_RUN", 

            # Configuration Processor Errors
            0x8A15C101 :"WINGET_CONFIG_ERROR_UNIT_NOT_INSTALLED", 
            0x8A15C102 :"WINGET_CONFIG_ERROR_UNIT_NOT_FOUND_REPOSITORY", 
            0x8A15C103 :"WINGET_CONFIG_ERROR_UNIT_MULTIPLE_MATCHES", 
            0x8A15C104 :"WINGET_CONFIG_ERROR_UNIT_INVOKE_GET", 
            0x8A15C105 :"WINGET_CONFIG_ERROR_UNIT_INVOKE_TEST", 
            0x8A15C106 :"WINGET_CONFIG_ERROR_UNIT_INVOKE_SET", 
            0x8A15C107 :"WINGET_CONFIG_ERROR_UNIT_MODULE_CONFLICT", 
            0x8A15C108 :"WINGET_CONFIG_ERROR_UNIT_IMPORT_MODULE", 
            0x8A15C109 :"WINGET_CONFIG_ERROR_UNIT_INVOKE_INVALID_RESULT", 
            0x8A15C110 :"WINGET_CONFIG_ERROR_UNIT_SETTING_CONFIG_ROOT", 
            0x8A15C111 :"WINGET_CONFIG_ERROR_UNIT_IMPORT_MODULE_ADMIN", 
            0x8A15C112 :"WINGET_CONFIG_ERROR_NOT_SUPPORTED_BY_PROCESSOR"            
                }
        
        returnText: str = hex(returncode)
        if (returncode in dict):
            returnText = returnText + ":" + dict[returncode]

        return returnText

    def getPackagesForQuery(self, query: str) -> list[Package]:
        print(f"🔵 Starting {self.NAME} search for dynamic packages")
        packages: list[Package] = []
        rawOutput = f"\n\n------- Winget query {query}"
        try:
            p = subprocess.Popen([self.EXECUTABLE, "search", query, "--accept-source-agreements"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, shell=True)
            hasShownId: bool = False
            idPosition: int = 0
            versionPosition: int = 0
            noSourcesAvailable: bool = False
            while p.poll() is None:
                line: str = str(p.stdout.readline().strip(), "utf-8", errors="ignore")
                if line:
                    rawOutput += line
                    if not hasShownId:
                        if " Id " in line:
                            line = line.replace("\x08-\x08\\\x08|\x08 \r", "")
                            for char in ("\r", "/", "|", "\\", "-"):
                                line = line.split(char)[-1].strip()
                            hasShownId = True
                            idPosition = len(line.split("Id")[0])
                            versionPosition = len(line.split("Version")[0])
                            sourcePosition = len(line.split("Source")[0])
                            if len(line) == sourcePosition:
                                noSourcesAvailable = True
                                print("🟡 Winget reported no sources on getPackagesForQuery")

                    elif "---" in line:
                        pass
                    else:
                        try:
                            name = line[0:idPosition].strip()
                            idVersionSubstr = line[idPosition:].strip()
                            if "  " in name:
                                oName = name
                                while "  " in oName:
                                    oName = oName.replace("  ", " ")
                                idVersionSubstr = oName.split(" ")[-1] + idVersionSubstr
                                name = " ".join(oName.split(" ")[:-1])
                            idVersionSubstr.replace("\t", " ")
                            while "  " in idVersionSubstr:
                                idVersionSubstr = idVersionSubstr.replace("  ", " ")
                            iOffset = 0
                            id = idVersionSubstr.split(" ")[iOffset]
                            ver = idVersionSubstr.split(" ")[iOffset + 1]
                            if not noSourcesAvailable:
                                source = "Winget: " + idVersionSubstr.split(" ")[iOffset + 2]
                            if len(id) == 1:
                                iOffset + 1
                                id = idVersionSubstr.split(" ")[iOffset]
                                ver = idVersionSubstr.split(" ")[iOffset + 1]
                                if not noSourcesAvailable:
                                    source = "Winget: " + idVersionSubstr.split(" ")[iOffset + 2]
                            if ver.strip() in ("<", "-"):
                                iOffset += 1
                                ver = ver.strip() + " " + idVersionSubstr.split(" ")[iOffset + 1]
                                if not noSourcesAvailable:
                                    source = "Winget: " + idVersionSubstr.split(" ")[iOffset + 2]

                            if noSourcesAvailable:
                                if "msstore" in line:
                                    source = "Winget: msstore"
                                elif "winget" in line:
                                    source = "Winget: winget"
                                else:
                                    source = "Winget"

                            elif source.strip() == "":
                                if "msstore" in line:
                                    source = "Winget: msstore"
                                elif "winget" in line:
                                    source = "Winget: winget"
                                elif len(Globals.wingetSources.keys() >= 0):
                                    source = "Winget: " + list(Globals.wingetSources.keys())[0]
                                else:
                                    source = "Winget"

                            if "Tag" in source or "Moniker" in source or "Command" in source:
                                if "msstore" in line:
                                    source = "Winget: msstore"
                                elif "winget" in line:
                                    source = "Winget: winget"
                                else:
                                    source = "Winget"

                            source = source.strip()

                            if "  " not in name:
                                if name not in self.BLACKLISTED_PACKAGE_NAMES and id not in self.BLACKLISTED_PACKAGE_IDS and version not in self.BLACKLISTED_PACKAGE_VERSIONS:
                                    packages.append(Package(name, id, ver, source, Winget))
                            else:
                                if name not in self.BLACKLISTED_PACKAGE_NAMES and id not in self.BLACKLISTED_PACKAGE_IDS and version not in self.BLACKLISTED_PACKAGE_VERSIONS:
                                    name = name.replace("  ", "#").replace("# ", "#").replace(" #", "#")
                                    while "##" in name:
                                        name = name.replace("##", "#")
                                    print(f"🟡 package {name} failed parsing, going for method 2...")
                                    packages.append(Package(name, id, ver, source, Winget))
                        except Exception as e:
                            report(e)
                            packages.append(Package(line[0:idPosition].strip(), line[idPosition:versionPosition].strip(), line[versionPosition:sourcePosition].strip(), f"Winget: {line[sourcePosition:].strip()}", Winget))
                            if type(e) is not IndexError:
                                report(e)
            exitCode: int = p.returncode
            if exitCode == 0:
                print(f"🟢 {self.NAME} query for packages finished with {len(packages)} result(s)")
            else:
                exitText = self.convertWingetReturnCode(exitCode)
                print(f"🟠 {self.NAME} query for packages had errors - returncode {exitText}")

            Globals.PackageManagerOutput += rawOutput
            return packages

        except Exception as e:
            report(e)
            return packages

    def getAvailableUpdates(self) -> list[UpgradablePackage]:
        f"""
        Will retieve the upgradable packages by {self.NAME} in the format of a list[UpgradablePackage] object.
        """
        print(f"🔵 Starting {self.NAME} search for updates")
        try:
            packages: list[UpgradablePackage] = []
            p = subprocess.Popen([self.EXECUTABLE, "upgrade", "--include-unknown", "--accept-source-agreements"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, cwd=os.getcwd(), env=os.environ.copy(), shell=True)
            hasShownId: bool = False
            idPosition: int = 0
            versionPosition: int = 0
            newVerPosition: int = 0
            rawoutput = "\n\n---------" + self.NAME
            noSourcesAvailable = False
            while p.poll() is None:
                line: str = str(p.stdout.readline().strip(), "utf-8", errors="ignore")
                rawoutput += "\n" + line
                if not hasShownId:
                    if " Id " in line:
                        line = line.replace("\x08-\x08\\\x08|\x08 \r", "")
                        for char in ("\r", "/", "|", "\\", "-"):
                            line = line.split(char)[-1].strip()
                        hasShownId = True
                        idPosition = len(line.split("Id")[0])
                        versionPosition = len(line.split("Version")[0])
                        newVerPosition = len(line.split("Available")[0])
                        sourcePosition = len(line.split("Source")[0])
                        if len(line) == sourcePosition:
                            noSourcesAvailable = True
                            print("🟡 Winget reported no sources on getAvailableUpdates")
                    else:
                        pass
                elif "---" in line:
                    pass
                elif " upgrades available." in line:
                    hasShownId = False
                else:
                    element = line
                    try:
                        verElement = element[idPosition:].strip()
                        verElement.replace("\t", " ")
                        while "  " in verElement:
                            verElement = verElement.replace("  ", " ")
                        iOffset = 0
                        id = verElement.split(" ")[iOffset]
                        ver = verElement.split(" ")[iOffset + 1]
                        newver = verElement.split(" ")[iOffset + 2]
                        if not noSourcesAvailable:
                            source = "Winget: " + verElement.split(" ")[iOffset + 3]
                        if len(id) == 1:
                            iOffset + 1
                            id = verElement.split(" ")[iOffset]
                            ver = verElement.split(" ")[iOffset + 1]
                            newver = verElement.split(" ")[iOffset + 2]
                            if not noSourcesAvailable:
                                source = "Winget: " + verElement.split(" ")[iOffset + 3]
                        if ver.strip() in ("<", ">", "-"):
                            iOffset += 1
                            ver = ver.strip() + " " + verElement.split(" ")[iOffset + 1]
                            newver = verElement.split(" ")[iOffset + 2]
                            if not noSourcesAvailable:
                                source = "Winget: " + verElement.split(" ")[iOffset + 3]
                        name = element[0:idPosition].strip()

                        if noSourcesAvailable:
                            source = "Winget"
                        elif source.strip() == "":
                            if len(list(Globals.wingetSources.keys()) >= 0):
                                print("🟠 No source found on Winget.getAvailableUpdates()!")
                                source = "Winget: " + list(Globals.wingetSources.keys())[0]
                            else:
                                source = "Winget"

                        if "  " not in name:
                            if name not in self.BLACKLISTED_PACKAGE_NAMES and id not in self.BLACKLISTED_PACKAGE_IDS and version not in self.BLACKLISTED_PACKAGE_VERSIONS:
                                packages.append(UpgradablePackage(name, id, ver, newver, source, Winget))
                        else:
                            name = name.replace("  ", "#").replace("# ", "#").replace(" #", "#")
                            while "##" in name:
                                name = name.replace("##", "#")
                            if name not in self.BLACKLISTED_PACKAGE_NAMES and id not in self.BLACKLISTED_PACKAGE_IDS and version not in self.BLACKLISTED_PACKAGE_VERSIONS:
                                packages.append(UpgradablePackage(name.split("#")[0], name.split("#")[-1] + id, ver, newver, source, Winget))
                    except Exception as e:
                        packages.append(UpgradablePackage(element[0:idPosition].strip(), element[idPosition:versionPosition].strip(), element[versionPosition:newVerPosition].split(" ")[0].strip(), element[newVerPosition:sourcePosition].split(" ")[0].strip(), "Winget: " + element[sourcePosition:].split(" ")[0].strip(), Winget))
                        if type(e) is not IndexError:
                            report(e)
            exitCode: int = p.returncode
            if exitCode == 0:
                print(f"🟢 {self.NAME} search for updates finished with {len(packages)} result(s)")
            else:
                exitText = self.convertWingetReturnCode(exitCode)
                print(f"🟠 {self.NAME} search for updates had errors - returncode {exitText}")
            Globals.PackageManagerOutput += rawoutput
            return packages
        except Exception as e:
            report(e)
            return []

    def getInstalledPackages(self, second_attempt: bool = False) -> list[Package]:
        f"""
        Will retieve the intalled packages by {self.NAME} in the format of a list[Package] object.
        """

        def getSource(id: str) -> str:
            id = id.strip()
            androidValid = True
            for letter in id:
                if letter not in "abcdefghijklmnopqrstuvwxyz.":
                    androidValid = False
            if androidValid and id.count(".") > 1:
                return _("Android Subsystem")
            s = "Winget"
            for illegal_char in ("{", "}", " "):
                if illegal_char in id:
                    s = _("Local PC")
                    break
            if s == "Winget":
                if id.count(".") != 1:
                    s = (_("Local PC"))
                    if id.count(".") > 1:
                        for letter in id:
                            if letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
                                s = "Winget"
                                break
            if s == _("Local PC"):
                if id == "Steam":
                    s = "Steam"
                if id.count("Steam App ") == 1:
                    s = "Steam"
                    for number in id.split("Steam App ")[1]:
                        if number not in "0123456789":
                            s = _("Local PC")
                            break
                if id == "Uplay":
                    s = "Ubisoft Connect"
                if id.count("Uplay Install ") == 1:
                    s = "Ubisoft Connect"
                    for number in id.split("Uplay Install ")[1]:
                        if number not in "0123456789":
                            s = _("Local PC")
                            break
                if id.count("_is1") == 1:
                    s = "GOG"
                    for number in id.split("_is1")[0]:
                        if number not in "0123456789":
                            s = _("Local PC")
                            break
                    if len(id) != 14:
                        s = _("Local PC")
                    if id.count("GOG") == 1:
                        s = "GOG"
            if s == "Winget":
                if len(id.split("_")[-1]) in (13, 14) and (len(id.split("_")) == 2 or id == id.upper()):
                    s = "Microsoft Store"
                elif len(id.split("_")[-1]) <= 13 and len(id.split("_")) == 2 and "…" == id.split("_")[-1][-1]:  # Delect microsoft store ellipsed packages
                    s = "Microsoft Store"
            if len(id) in (13, 14) and (id.upper() == id):
                s = "Winget: msstore"
            if s == "Winget":
                s = "Winget: winget"
            return s

        print(f"🔵 Starting {self.NAME} search for installed packages")
        try:
            packages: list[Package] = []
            p = subprocess.Popen([self.EXECUTABLE, "list", "--accept-source-agreements"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, cwd=os.getcwd(), env=os.environ.copy(), shell=True)
            hasShownId: bool = False
            idPosition: int = 0
            versionPosition: int = 0
            rawoutput = "\n\n---------" + self.NAME
            while p.poll() is None:
                line: str = str(p.stdout.readline().strip(), "utf-8", errors="ignore")
                rawoutput += "\n" + line
                if not hasShownId:
                    if " Id " in line:
                        line = line.replace("\x08-\x08\\\x08|\x08 \r", "")
                        for char in ("\r", "/", "|", "\\", "-"):
                            line = line.split(char)[-1].strip()
                        hasShownId = True
                        idPosition = len(line.split("Id")[0])
                        versionPosition = len(line.split("Version")[0])
                        sourcePosition = len(line.split("Source")[0])
                    else:
                        pass
                elif "---" in line:
                    pass
                else:
                    packageLine = line.replace("2010  x", "2010 x").replace("Microsoft.VCRedist.2010", " Microsoft.VCRedist.2010")  # Fix an issue with MSVC++ 2010, where it shows with a double space (see https://github.com/marticliment/WingetUI#450)
                    try:
                        verElement = packageLine[idPosition:].strip()
                        verElement.replace("\t", " ")
                        untrimmedVerelement = verElement
                        while "  " in verElement:
                            verElement = verElement.replace("  ", " ")
                        iOffset = 0
                        id = " ".join(untrimmedVerelement.split(" ")[iOffset:-1])
                        ver = verElement.split(" ")[-1]
                        if len(id) > (versionPosition - idPosition):
                            id = " ".join(untrimmedVerelement.split(" ")[iOffset])
                            id = id.replace("  ", "#").replace(" ", "").replace("#", " ")
                            ver = verElement.split(" ")[iOffset + 1]
                        if len(id) == 1:
                            iOffset + 1
                            id = verElement.split(" ")[iOffset]
                            ver = verElement.split(" ")[iOffset + 1]
                        if ver.strip() in ("<", "-", ">"):
                            iOffset += 1
                            ver = ver.strip() + " " + verElement.split(" ")[iOffset + 1]
                        name = packageLine[0:idPosition].strip()

                        if name.strip() == "":
                            continue

                        if packageLine.strip().split(" ")[-1] in Globals.wingetSources.keys():
                            source = "Winget: " + packageLine.split(" ")[-1]
                        else:
                            source = getSource(id)

                        if "  " not in name:
                            if name not in self.BLACKLISTED_PACKAGE_NAMES and not id.strip() in self.BLACKLISTED_PACKAGE_IDS and version not in self.BLACKLISTED_PACKAGE_VERSIONS:
                                packages.append(Package(name, id.strip(), ver, source, Winget))
                        else:
                            if name not in self.BLACKLISTED_PACKAGE_NAMES and not id.strip() in self.BLACKLISTED_PACKAGE_IDS and version not in self.BLACKLISTED_PACKAGE_VERSIONS:
                                print(f"🟡 package {name} failed parsing, going for method 2...")
                                name = name.replace("  ", "#").replace("# ", "#").replace(" #", "#")
                                while "##" in name:
                                    name = name.replace("##", "#")
                                packages.append(Package(name.split("#")[0], (name.split("#")[-1] + id).strip(), ver, source, Winget))
                    except Exception as e:
                        packages.append(Package(packageLine[0:idPosition].strip(), packageLine[idPosition:versionPosition].strip(), packageLine[versionPosition:sourcePosition].strip(), "Winget: " + packageLine[sourcePosition:].strip(), Winget))
                        if type(e) is not IndexError:
                            report(e)
            exitCode: int = p.returncode
            if exitCode == 0:
                print(f"🟢 {self.NAME} search for installed packages finished with {len(packages)} result(s)")
            else:
                exitText = self.convertWingetReturnCode(exitCode)
                print(f"🟠 {self.NAME} search for installed packages had errors - returncode {exitText}")

            Globals.PackageManagerOutput += rawoutput

            if len(packages) <= 2 and not second_attempt:
                print("🟠 Chocolatey got too few installed packages, retrying")
                return self.getInstalledPackages(second_attempt=True)

            return packages
        except Exception as e:
            report(e)
            return []

    def getPackageDetails(self, package: Package) -> PackageDetails:
        """
        Will return a PackageDetails object containing the information of the given Package object
        """
        print(f"🔵 Starting get info for {package.Id} on {self.NAME}")
        if "…" in package.Id:
            self.updatePackageId(package)
        details = PackageDetails(package)
        try:
            details.Scopes = [_("Current user"), _("Local machine")]
            details.ManifestUrl = f"https://github.com/microsoft/winget-pkgs/tree/master/manifests/{package.Id[0].lower()}/{'/'.join(package.Id.split('.'))}" if not (package.Id == package.Id.upper()) else f"https://apps.microsoft.com/store/detail/{package.Id}"
            details.Architectures = ["x64", "x86"] + (["arm64"] if self.IS_ARM else [])
            loadedInformationPieces = 0
            currentIteration = 0
            while loadedInformationPieces < 2 and currentIteration < 50:
                currentIteration += 1
                outputIsDescribing = False
                outputIsShowingNotes = False
                outputIsShowingTags = False
                p = subprocess.Popen([self.EXECUTABLE, "show", "--id", f"{package.Id}", "--exact", "--accept-source-agreements", "--locale", locale.getdefaultlocale()[0].replace("_", "-")], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, cwd=os.getcwd(), env=os.environ.copy(), shell=True)
                output: list[str] = []
                foundInstallers = True
                while p.poll() is None:
                    line = p.stdout.readline()
                    if line:
                        if b"No package found matching input criteria." in line:
                            return details
                        elif b"No applicable installer found; see logs for more details." in line:
                            foundInstallers = False
                            print(f"🟡 Couldn't found installers for locale {locale.getdefaultlocale()[0]}")
                        elif b"The value provided for the `locale` argument is invalid" in line:
                            foundInstallers = False
                            print(f"🟠 The locale {locale.getdefaultlocale()[0]} was tagged as invalid!")
                        output.append(str(line, encoding='utf-8', errors="ignore"))

                if not foundInstallers:
                    p = subprocess.Popen([self.EXECUTABLE, "show", "--id", f"{package.Id}", "--exact", "--accept-source-agreements", "--locale", "en-US"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, cwd=os.getcwd(), env=os.environ.copy(), shell=True)
                    output: list[str] = []
                    foundInstallers = True
                    while p.poll() is None:
                        line = p.stdout.readline()
                        if line:
                            if b"No package found matching input criteria." in line:
                                return details
                            elif b"No applicable installer found; see logs for more details." in line:
                                foundInstallers = False
                                print("🟠 Couldn't found installers for locale en_US")
                            output.append(str(line, encoding='utf-8', errors="ignore"))

                if not foundInstallers:
                    p = subprocess.Popen([self.EXECUTABLE, "show", "--id", f"{package.Id}", "--exact", "--accept-source-agreements"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, cwd=os.getcwd(), env=os.environ.copy(), shell=True)
                    output: list[str] = []
                    foundInstallers = True
                    while p.poll() is None:
                        line = p.stdout.readline()
                        if line:
                            if b"No package found matching input criteria." in line:
                                return details
                            elif b"No applicable installer found; see logs for more details." in line:
                                foundInstallers = False
                                break
                            output.append(str(line, encoding='utf-8', errors="ignore"))

                Globals.PackageManagerOutput += "\n--------" + "\n".join(output)

                for line in output:
                    if line[0] == " " and outputIsDescribing:
                        details.Description += "<br>" + line[2:]
                    else:
                        outputIsDescribing = False
                    if line[0] == " " and outputIsShowingNotes:
                        details.ReleaseNotes += line[2:] + "<br>"
                    else:
                        outputIsShowingNotes = False
                    if line[0] == " " and outputIsShowingTags:
                        details.Tags.append(line.strip())
                    else:
                        outputIsShowingTags = False
                    if "Publisher:" in line:
                        details.Publisher = line.replace("Publisher:", "").strip()
                        loadedInformationPieces += 1
                    elif "Description:" in line:
                        details.Description = line.replace("Description:", "").strip()
                        outputIsDescribing = True
                        loadedInformationPieces += 1
                    elif "Author:" in line:
                        details.Author = line.replace("Author:", "").strip()
                        loadedInformationPieces += 1
                    elif "Homepage:" in line:
                        details.HomepageURL = line.replace("Homepage:", "").strip()
                        loadedInformationPieces += 1
                    elif "License:" in line:
                        details.License = line.replace("License:", "").strip()
                        loadedInformationPieces += 1
                    elif "License Url:" in line:
                        details.LicenseURL = line.replace("License Url:", "").strip()
                        loadedInformationPieces += 1
                    elif "Installer SHA256:" in line:
                        details.InstallerHash = line.replace("Installer SHA256:", "").strip()
                        loadedInformationPieces += 1
                    elif "Installer Url:" in line:
                        details.InstallerURL = line.replace("Installer Url:", "").strip()
                        try:
                            details.InstallerSize = int(urlopen(details.InstallerURL).length / 1000000)
                        except Exception as e:
                            print("🟠 Can't get installer size:", type(e), str(e))
                        loadedInformationPieces += 1
                    elif "Release Date:" in line:
                        details.UpdateDate = line.replace("Release Date:", "").strip()
                        loadedInformationPieces += 1
                    elif "Release Notes Url:" in line:
                        details.ReleaseNotesUrl = line.replace("Release Notes Url:", "").strip()
                        loadedInformationPieces += 1
                    elif "Release Notes:" in line:
                        details.ReleaseNotes = ""
                        outputIsShowingNotes = True
                        loadedInformationPieces += 1
                    elif "Tags:" in line:
                        details.Tags = []
                        outputIsShowingTags = True
                        loadedInformationPieces += 1
                    elif "Installer Type:" in line:
                        details.InstallerType = line.replace("Installer Type:", "").strip()

            details.Description = ConvertMarkdownToHtml(details.Description)
            details.ReleaseNotes = ConvertMarkdownToHtml(details.ReleaseNotes)

            print(f"🔵 Loading versions for {package.Name}")
            currentIteration = 0
            versions = []
            while versions == [] and currentIteration < 50:
                currentIteration += 1
                p = subprocess.Popen([self.EXECUTABLE, "show", "--id", f"{package.Id}", "-e", "--versions", "--accept-source-agreements"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, cwd=os.getcwd(), env=os.environ.copy(), shell=True)
                foundDashes = False
                while p.poll() is None:
                    line = p.stdout.readline().strip()
                    if line:
                        if foundDashes:
                            versions.append(str(line, encoding='utf-8', errors="ignore"))
                        elif b"--" in line:
                            foundDashes = True
            details.Versions = versions
            print(f"🟢 Get info finished for {package.Name} on {self.NAME}")
            return details
        except Exception as e:
            report(e)
            return details

    def getIcon(self, source: str) -> QIcon:
        if not self.LoadedIcons:
            self.LoadedIcons = True
            self.wingetIcon = QIcon(getMedia("winget"))
            self.localIcon = QIcon(getMedia("localpc"))
            self.msStoreIcon = QIcon(getMedia("msstore"))
            self.wsaIcon = QIcon(getMedia("android"))
            self.steamIcon = QIcon(getMedia("steam"))
            self.gogIcon = QIcon(getMedia("gog"))
            self.uPlayIcon = QIcon(getMedia("uplay"))
        if "microsoft store" in source.lower():
            return self.msStoreIcon
        elif source in (_("Local PC"), "Local PC"):
            return self.localIcon
        elif "steam" in source.lower():
            return self.steamIcon
        elif "gog" in source.lower():
            return self.gogIcon
        elif "ubisoft connect" in source.lower():
            return self.uPlayIcon
        elif source in (_("Android Subsystem"), "Android Subsystem"):
            return self.wsaIcon
        else:
            return self.wingetIcon

    def getParameters(self, options: InstallationOptions, isAnUninstall: bool = False) -> list[str]:
        Parameters: list[str] = ["--accept-source-agreements"]
        if not isAnUninstall:
            if options.Architecture:
                Parameters += ["--architecture", options.Architecture]
            if options.SkipHashCheck:
                Parameters.append("--ignore-security-hash")
            if options.CustomInstallLocation != "":
                Parameters += ["--location", options.CustomInstallLocation]
        if options.CustomParameters:
            Parameters += options.CustomParameters
        if options.InstallationScope:
            if options.InstallationScope in (_("Current user"), "Current user"):
                Parameters.append("--scope")
                Parameters.append("user")
            elif options.InstallationScope in (_("Local machine"), "Local machine"):
                Parameters.append("--scope")
                Parameters.append("machine")
        if options.InteractiveInstallation:
            Parameters.append("--interactive")
        else:
            Parameters.append("--disable-interactivity")
        if options.Version:
            Parameters += ["--version", options.Version, "--force"]
        return Parameters

    def startInstallation(self, package: Package, options: InstallationOptions, widget: 'PackageInstallerWidget') -> subprocess.Popen:
        if "…" in package.Id:
            self.updatePackageId(package)

        if "64" in package.Name or "64" in package.Id:
            print(f"🟠 Forcing 64bit architecture for package {package.Id}, {package.Name}")
            options.Architecture = "x64"
        elif ".x86" in package.Id or "32-bit" in package.Name:
            print(f"🟠 Forcing 32bit architecture for package {package.Id}, {package.Name}")
            options.Architecture = "x86"

        Command = [self.EXECUTABLE, "install"] + (["--id", package.Id, "--exact"] if "…" not in package.Id else ["--name", '"' + package.Name + '"']) + self.getParameters(options) + ["--accept-package-agreements"]
        if options.RunAsAdministrator:
            Command = [GSUDO_EXECUTABLE] + Command
        print(f"🔵 Starting {package} installation with Command", Command)
        p = subprocess.Popen(Command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, shell=True, cwd=GSUDO_EXE_LOCATION, env=os.environ)
        Thread(target=self.installationThread, args=(p, options, widget,), name=f"{self.NAME} installation thread: installing {package.Name}").start()
        return p

    def startUpdate(self, package: Package, options: InstallationOptions, widget: 'PackageInstallerWidget') -> subprocess.Popen:
        if "…" in package.Id:
            self.updatePackageId(package)

        if "64-bit" in package.Name or "x64" in package.Id.lower():
            print(f"🟠 Forcing 64bit architecture for package {package.Id}, {package.Name}")
            options.Architecture = "x64"
        elif "32-bit" in package.Name or "x86" in package.Id.lower():
            print(f"🟠 Forcing 32bit architecture for package {package.Id}, {package.Name}")
            options.Architecture = "x86"

        Command = [self.EXECUTABLE, "upgrade"] + (["--id", package.Id, "--exact"] if "…" not in package.Id else ["--name", '"' + package.Name + '"']) + ["--include-unknown"] + self.getParameters(options) + ["--accept-package-agreements"]
        if options.RunAsAdministrator:
            Command = [GSUDO_EXECUTABLE] + Command
        print(f"🔵 Starting {package} update with Command", Command)
        p = subprocess.Popen(Command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, shell=True, cwd=GSUDO_EXE_LOCATION, env=os.environ)
        Thread(target=self.installationThread, args=(p, options, widget,), name=f"{self.NAME} installation thread: update {package.Name}").start()
        return p

    def installationThread(self, p: subprocess.Popen, options: InstallationOptions, widget: 'PackageInstallerWidget'):
        output = ""
        counter = 0
        while p.poll() is None:
            line, is_newline = getLineFromStdout(p)
            line = str(line, encoding='utf-8', errors="ignore").strip()
            if line:
                widget.addInfoLine.emit((line, is_newline))
                counter += 1
                widget.counterSignal.emit(counter)
                if is_newline:
                    output += line + "\n"
        p.wait()
        match p.returncode:
            case 0x8A150011:
                outputCode = RETURNCODE_INCORRECT_HASH
            case 0x8A150109:  # need restart
                outputCode = RETURNCODE_NEEDS_RESTART
            case other:
                outputCode = other
        if "No applicable upgrade found" in output or "No newer package versions are available from the configured sources" in output:
            outputCode = RETURNCODE_NO_APPLICABLE_UPDATE_FOUND
        widget.finishInstallation.emit(outputCode, output)

    def startUninstallation(self, package: Package, options: InstallationOptions, widget: 'PackageInstallerWidget') -> subprocess.Popen:
        if "…" in package.Id:
            self.updatePackageId(package, installed=True)

        if "64" in package.Name or "64" in package.Id:
            print(f"🟠 Forcing 64bit architecture for package {package.Id}, {package.Name}")
            options.Architecture = "x64"
        elif ".x86" in package.Id or "32-bit" in package.Name:
            print(f"🟠 Forcing 32bit architecture for package {package.Id}, {package.Name}")
            options.Architecture = "x86"

        Command = [self.EXECUTABLE, "uninstall"] + (["--id", package.Id, "--exact"] if "…" not in package.Id else ["--name", '"' + package.Name + '"']) + self.getParameters(options, True)
        if options.RunAsAdministrator:
            Command = [GSUDO_EXECUTABLE] + Command
        print(f"🔵 Starting {package} uninstall with Command", Command)
        p = subprocess.Popen(Command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, shell=True, cwd=GSUDO_EXE_LOCATION, env=os.environ)
        Thread(target=self.uninstallationThread, args=(p, options, widget,), name=f"{self.NAME} installation thread: uninstall {package.Name}").start()
        return p

    def uninstallationThread(self, p: subprocess.Popen, options: InstallationOptions, widget: 'PackageInstallerWidget'):
        counter = RETURNCODE_OPERATION_SUCCEEDED
        output = ""
        while p.poll() is None:
            line, is_newline = getLineFromStdout(p)
            line = str(line, encoding='utf-8', errors="ignore").strip()
            if line:
                widget.addInfoLine.emit((line, is_newline))
                counter += 1
                widget.counterSignal.emit(counter)
                if is_newline:
                    output += line + "\n"
        p.wait()
        outputCode = p.returncode
        if "1603" in output or "0x80070005" in output or "Access is denied" in output:
            outputCode = RETURNCODE_NEEDS_ELEVATION
        widget.finishInstallation.emit(outputCode, output)

    def updatePackageId(self, package: Package, installed: bool = False) -> tuple[str, str]:
        if not installed:
            p = subprocess.Popen([self.EXECUTABLE, "search", "--name", package.Name.replace("…", ""), "--accept-source-agreements"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, cwd=os.getcwd(), env=os.environ.copy(), shell=True)
        else:
            p = subprocess.Popen([self.EXECUTABLE, "list", "--query", package.Name.replace("…", ""), "--accept-source-agreements"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, cwd=os.getcwd(), env=os.environ.copy(), shell=True)
        idSeparator = -1
        rawoutput = "\n\n" + " ".join(p.args)
        print(f"🔵 Finding Id for {package.Name} with command {p.args}")
        while p.poll() is None:
            line = p.stdout.readline()
            line = line.strip()
            if line:
                rawoutput += str(line, encoding='utf-8', errors="ignore") + "\n"
                if idSeparator == -1:
                    line = str(line, encoding='utf-8', errors="ignore").replace("\x08-\x08\\\x08|\x08 \r", "").split("\r")[-1]
                    if " Id " in line:
                        idSeparator = len(line.split("Id")[0])
                else:
                    if b"---" not in line:
                        newId = str(line, "utf-8", errors="ignore")[idSeparator:].split(" ")[0].strip()
                        print(line, idSeparator)
                        print("🔵 found Id", newId)
                        package.Id = newId
                        Globals.PackageManagerOutput += rawoutput + "\n\n"
                        return

        Globals.PackageManagerOutput += rawoutput + "\n\n"
        print("🟡 Better id not found!")

    def getSources(self) -> None:
        print(f"🔵 Starting {self.NAME} source search...")
        p = subprocess.Popen([self.EXECUTABLE, "source", "list"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, cwd=os.getcwd(), env=os.environ, shell=True)
        output = []
        dashesPassed = False
        sources: list[ManagerSource] = []
        while p.poll() is None:
            line = p.stdout.readline()
            line = line.strip()
            if line:
                if not dashesPassed:
                    if b"---" in line:
                        dashesPassed = True
                else:
                    output.append(str(line, encoding='utf-8', errors="ignore"))
        for element in output:
            try:
                while "  " in element.strip():
                    element = element.strip().replace("  ", " ")
                element: list[str] = element.split(" ")
                sources.append(ManagerSource(self, element[0].strip(), element[1].strip()))
            except Exception as e:
                report(e)
        print(f"🟢 {self.NAME} source search finished with {len(sources)} sources")
        return sources

    def installSource(self, source: ManagerSource, options: InstallationOptions, widget: 'PackageInstallerWidget') -> subprocess.Popen:
        Command = [GSUDO_EXECUTABLE, self.EXECUTABLE, "source", "add", "--name", source.Name, "--arg", source.Url, "--accept-source-agreements", "--disable-interactivity"]
        print(f"🔵 Starting source {source.Name} installation with Command", Command)
        p = subprocess.Popen(Command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, shell=True, cwd=GSUDO_EXE_LOCATION, env=os.environ)
        Thread(target=self.sourceProgressThread, args=(p, options, widget,), name=f"{self.NAME} installation thread: installing source {source.Name}").start()
        return p

    def uninstallSource(self, source: ManagerSource, options: InstallationOptions, widget: 'PackageInstallerWidget') -> subprocess.Popen:
        Command = [GSUDO_EXECUTABLE, self.EXECUTABLE, "source", "remove", "--name", source.Name, "--disable-interactivity"]
        print(f"🔵 Starting source {source.Name} removal with Command", Command)
        p = subprocess.Popen(Command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, shell=True, cwd=GSUDO_EXE_LOCATION, env=os.environ)
        Thread(target=self.sourceProgressThread, args=(p, options, widget,), name=f"{self.NAME} installation thread: installing source {source.Name}").start()
        return p

    def sourceProgressThread(self, p: subprocess.Popen, options: InstallationOptions, widget: 'PackageInstallerWidget'):
        output = ""
        counter = 0
        while p.poll() is None:
            line, is_newline = getLineFromStdout(p)
            line = str(line, encoding='utf-8', errors="ignore").strip()
            if line:
                widget.addInfoLine.emit((line, is_newline))
                counter += 1
                widget.counterSignal.emit(counter)
                if is_newline:
                    output += line + "\n"
        p.wait()
        widget.finishInstallation.emit(p.returncode, output)

    def detectManager(self, signal: Signal = None) -> None:
        o = subprocess.run([self.EXECUTABLE, "-v"], shell=True, stdout=subprocess.PIPE)
        Globals.componentStatus[f"{self.NAME}Found"] = shutil.which(self.EXECUTABLE) is not None
        Globals.componentStatus[f"{self.NAME}Version"] = o.stdout.decode('utf-8').replace("\n", " ").replace("\r", " ")
        if signal:
            signal.emit()
        Globals.wingetSources = {source.Name: source.Url for source in self.getSources()}

    def updateSources(self, signal: Signal = None) -> None:
        print(f"🔵 Reloading {self.NAME} sources...")
        subprocess.run([self.EXECUTABLE, "source", "update"], shell=True, stdout=subprocess.PIPE)
        if signal:
            signal.emit()


Winget = WingetPackageManager()
