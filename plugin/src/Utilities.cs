// Utilities.cs - Helper Functions
using System;
using System.IO;

namespace CADCopilot
{
    public class Utilities
    {
        private static string logFile = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
            "CADCopilot", "CADCopilot.log"
        );

        public static void LogInfo(string message)
        {
            WriteLog("INFO", message);
        }

        public static void LogError(string message, Exception ex = null)
        {
            string fullMessage = ex != null ? $"{message}: {ex.Message}" : message;
            WriteLog("ERROR", fullMessage);
        }

        public static void LogWarning(string message)
        {
            WriteLog("WARNING", message);
        }

        private static void WriteLog(string level, string message)
        {
            try
            {
                Directory.CreateDirectory(Path.GetDirectoryName(logFile));
                string logLine = $"[{DateTime.Now:yyyy-MM-dd HH:mm:ss}] [{level}] {message}";
                File.AppendAllText(logFile, logLine + Environment.NewLine);
            }
            catch { }
        }
    }
}