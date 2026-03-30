// Main.cs - AutoCAD Plugin Main Class
using Autodesk.AutoCAD.ApplicationServices;
using Autodesk.AutoCAD.Runtime;
using Autodesk.AutoCAD.Windows;
using System;
using System.Windows.Forms;

namespace CADCopilot
{
    public class CADCopilotPlugin : IExtensionApplication
    {
        private ChatUI chatWindow;
        private APIClient apiClient;
        
        public void Initialize()
        {
            try
            {
                // Initialize API client
                apiClient = new APIClient("http://localhost:8000");
                
                // Add ribbon button
                AddRibbonButton();
                
                // Log initialization
                Utilities.LogInfo("CAD Copilot initialized");
            }
            catch (Exception e)
            {
                Utilities.LogError("Initialization failed", e);
            }
        }
        
        public void Terminate()
        {
            try
            {
                if (chatWindow != null)
                {
                    chatWindow.Close();
                }
                Utilities.LogInfo("CAD Copilot terminated");
            }
            catch (Exception e)
            {
                Utilities.LogError("Termination error", e);
            }
        }
        
        [CommandMethod("CADCopilotOpen")]
        public void OpenCADCopilot()
        {
            try
            {
                if (chatWindow == null || chatWindow.IsDisposed)
                {
                    chatWindow = new ChatUI(apiClient);
                    chatWindow.Show();
                }
                else
                {
                    chatWindow.Focus();
                }
            }
            catch (Exception e)
            {
                Utilities.LogError("Open window error", e);
            }
        }
        
        private void AddRibbonButton()
        {
            // Placeholder for ribbon button creation
            // In real implementation, would add button to AutoCAD ribbon
        }
    }
}
