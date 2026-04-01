// Main.cs - AutoCAD Plugin Entry Point
using Autodesk.AutoCAD.ApplicationServices;
using Autodesk.AutoCAD.Runtime;
using System;

namespace CADCopilot
{
    public class CADCopilotPlugin : IExtensionApplication
    {
        private ChatUI chatWindow;
        private APIClient apiClient;

        // ✅ Points to your live Render API
        private const string API_URL = "https://cad-copilot-api.onrender.com";

        public void Initialize()
        {
            try
            {
                apiClient = new APIClient(API_URL);
                Utilities.LogInfo("CAD Copilot initialized");

                // Show welcome message in AutoCAD command line
                var doc = Application.DocumentManager.MdiActiveDocument;
                doc?.Editor.WriteMessage("\nCAD AI Copilot loaded! Type CADCOPILOT to open.\n");
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
                chatWindow?.Close();
                Utilities.LogInfo("CAD Copilot terminated");
            }
            catch (Exception e)
            {
                Utilities.LogError("Termination error", e);
            }
        }

        [CommandMethod("CADCOPILOT")]
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
                    chatWindow.BringToFront();
                    chatWindow.Focus();
                }
            }
            catch (Exception e)
            {
                Utilities.LogError("Open window error", e);
            }
        }
    }
}