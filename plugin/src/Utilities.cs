// Utilities.cs - Helper Functions
using System;
using System.IO;

namespace CADCopilot
{
    public class Utilities
    {
        private static string logFile = "CADCopilot.log";
        
        public static void LogInfo(string message)
        {
            WriteLog("INFO", message);
        }
        
        public static void LogError(string message, Exception ex = null)
        {
            string fullMessage = message;
            if (ex != null)
                fullMessage += ": " + ex.Message;
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
                string timestamp = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");
                string logLine = $"[{timestamp}] [{level}] {message}";
                
                File.AppendAllText(logFile, logLine + Environment.NewLine);
            }
            catch
            {
                // Silently fail if logging fails
            }
        }
    }
}
