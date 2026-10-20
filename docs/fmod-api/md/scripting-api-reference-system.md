# 26. Scripting API Reference | System

- Module: System

- system.require(fileName)

- system.backtrace()

- system.verbose(msg)

- system.print(msg)

- system.warn(msg)

- system.error(msg)

- system.message(msg)

- system.question(msg)

- system.getText(msg[, defaultText])

- system.getNumber(msg[, defaultText])

- system.start(pathToExecutable, processOptions)

- system.startAsync(pathToExecutable, processOptions)

- system.readDir(filePath, readDirFiltersFlag)

- system.readDirFilters

- system.getFile(filePath)

- system.openMode

- system.permission

- Class: File

- File.exists()

- File.open(openModeFlag)

- File.writeText(text)

- File.readText(maxSize)

- File.writeBinary(byteArray)

- File.readBinary(maxSize)

- File.close()

- File.copy(filePath)

- File.remove()

- File.size()

- File.permissions()

- File.setPermissions(permissions)

- Class: ScriptProcess

- ScriptProcess.isRunning()

- ScriptProcess.readAllStandardOutput()

- ScriptProcess.readAllStandardError()

- ScriptProcess.writeStandardInput(text, timeout)

- ScriptProcess.kill()

## Module: System

The `studio.system` module provides general system-wide functionality.

### system.require(fileName)

Loads a javascript file as a library. The `fileName` passed can be either a relative or absolute path. The file being loaded should contain a module. For example:

```
module.exports = {
    foobar: function() {
        // implementation
    },
};

```

The module can then be used:

```
var MyModule = studio.system.require("utils/file_name.js"); // absolute path or file path relative to the script
MyModule.foobar();

```

When loading relative module files, it is recommended that the modules are placed in a different folder, such as a subfolder. This ensures the module's files are not loaded as top-level script files. This loads scripts relative to the script making this call, so it is not possible to use `system.require` with relative paths from the console.

Returns the loaded js module object or `null` if unsuccessful.

### system.backtrace()

Returns the callstack as an array of strings.

### system.verbose(msg)

Logs a verbose message.

### system.print(msg)

Logs a message.

### system.warn(msg)

Logs a warning.

### system.error(msg)

Logs an error.

### system.message(msg)

Logs a message in a popup dialog (blocking).

### system.question(msg)

Prompts for a 'yes'/'no' response to a given message and returns a boolean value (blocking).

### system.getText(msg[, defaultText])

Prompts for text input and returns the string, or null if cancelled (blocking).

### system.getNumber(msg[, defaultText])

Prompts for numeric input and returns the value, or null if cancelled (blocking).

### system.start(pathToExecutable, processOptions)

Runs an external process with options object `{ workingDir, args, timeout (milliseconds) }` (blocking).

Returns a result object `{ exitCode, standardOutput, standardError }`.

### system.startAsync(pathToExecutable, processOptions)

Runs an external asynchronous process with options object `{ workingDir, args }`.

Returns a studio.system.ScriptProcess object representing the asynchronous process.

### system.readDir(filePath, readDirFiltersFlag)

Returns a string array from the filters specified by `readDirFiltersFlag` from the `filePath`. If `readDirFiltersFlag` is not defined in the function call, a default of `system.readDirFilters.AllEntries` will be used. The available options are described by the system.readDirFilters enum.

### system.readDirFilters

An enumeration used with `studio.system.readDir(filePath, readDirFiltersFlag)` to describe the filters in which a string array will be returned. The filter value is specified by combining values from the following list using the bitwise OR operator:

- `Dirs`: List directories that match the filters.

- `AllDirs`: List all directories; i.e. don't apply the filters to directory names.

- `Files`: List files.

- `Drives`: List disk drives (ignored under Unix).

- `NoSymLinks`: Do not list symbolic links (ignored by operating systems that don't support symbolic links).

- `NoDotAndDotDot`: Do not list the special entries "." and "..".

- `NoDot`: Do not list the special entry ".".

- `NoDotDot`: Do not list the special entry "..".

- `AllEntries`: List directories, files, drives and symlinks (this does not list broken symlinks unless you specify System).

- `Readable`: List files for which the application has read access. The Readable value needs to be combined with Dirs or Files.

- `Writable`: List files for which the application has write access. The Writable value needs to be combined with Dirs or Files.

- `Executable`: List files for which the application has execute access. The Executable value needs to be combined with Dirs or Files.

- `Modified`: Only list files that have been modified (ignored on Unix).

- `Hidden`: List hidden files (on Unix, files starting with a ".").

- `System`: List system files (on Unix, FIFOs, sockets and device files are included; on Windows, .lnk files are included).

- `CaseSensitive`: The filter should be case sensitive.

### system.getFile(filePath)

Returns a studio.system.File object representing the file at `filePath`.

### system.openMode

An enumeration used with `studio.system.File.open()` to describe the mode in which a file is opened. Possible values are:

- `ReadOnly`: The file is open for reading.

- `WriteOnly`: The file is open for writing. This mode implies `Truncate`.

- `ReadWrite`: The file is open for reading and writing.

- `Append`: The file is opened in append mode so that all data is written to the end of the file.

- `Truncate`: If possible, the file is truncated before it is opened. All earlier contents of the file are lost.

### system.permission

An enumeration used with studio.system.File.setPermissions() to alter the permissions of a file. The permissions of a file can be queried using studio.system.File.permissions. The values may be OR-ed together to test multiple permissions and ownership values. Possible values are:

- `ReadOwner`: The file is readable by the owner of the file.

- `WriteOwner`: The file is writable by the owner of the file.

- `ExeOwner`: The file is executable by the owner of the file.

- `ReadUser`: The file is readable by the user (platform-dependent).

- `WriteUser`: The file is writable by the user (platform-dependent).

- `ExeUser`: The file is executable by the user (platform-dependent).

- `ReadGroup`: The file is readable by the group.

- `WriteGroup`: The file is writable by the group.

- `ExeGroup`: The file is executable by the group.

- `ReadOther`: The file is readable by anyone.

- `WriteOther`: The file is writable by anyone.

- `ExeOther`: The file is executable by anyone.

- `Exe`: The file is executable by everyone.

- `Write`: The file is writable by everyone.

- `Read`: The file is readable by everyone.

## Class: File

The `studio.system.File` object allows for interaction with files on disk. A `studio.system.File` can be created using system.getFile().

### File.exists()

Returns `true` if the file the object represents exists on disk, or `false` otherwise.

### File.open(openModeFlag)

Opens the file in the mode specified by `openModeFlag`. The available options are described by the system.openMode enum. Returns `true` if the operation succeeds, or `false` otherwise.

### File.writeText(text)

Writes the `text` to the file as Utf8. Returns the number of bytes that were actually written, or -1 if an error occurred.

### File.readText(maxSize)

Reads at most `maxSize` bytes from the file as Utf8 and returns the resulting string.

### File.writeBinary(byteArray)

Writes the `byteArray` to the file. Returns the number of bytes that were actually written, or -1 if an error occurred.

### File.readBinary(maxSize)

Reads at most `maxSize` bytes from the file and returns the result.

### File.close()

Closes the file and flushes any changes to disk. Returns `true` if the operation succeeds, or `false` otherwise.

### File.copy(filePath)

Copies the file to the absolute `filePath` specified. Directories that don't exist within the `filePath` will be created as required.

### File.remove()

Removes the file from disk. The operation is not undoable and the file will not be recoverable from the Recycle Bin on Windows or the Trash on Mac OS X. Returns `true` if the operation succeeds, or `false` otherwise.

### File.size()

Returns the size of the file in bytes.

### File.permissions()

Returns the complete OR-ed together combination of system.permission flags if the file exists on disk, or 0 otherwise.

### File.setPermissions(permissions)

Sets the system.permission flags for the file to the `permissions` specified. Returns true if successful, or false if the permissions cannot be modified.

## Class: ScriptProcess

The `studio.system.ScriptProcess` object allows for interaction with a process started using system.startAsync().

### ScriptProcess.isRunning()

Returns `true` if the process is running and is ready for reading or writing, or `false` otherwise.

### ScriptProcess.readAllStandardOutput()

Returns all data available from the standard output of the process.

### ScriptProcess.readAllStandardError()

Returns all data available from the standard error of the process.

### ScriptProcess.writeStandardInput(text, timeout)

Writes the `text` to the standard input of the process and waits up to `timeout` number of milliseconds for the process to write back to the standard output.

### ScriptProcess.kill()

Kills the process, causing it to exit immediately.

FMOD Studio User Manual 2.03.15 (2026-09-21). © 2026 Firelight Technologies Pty Ltd.
