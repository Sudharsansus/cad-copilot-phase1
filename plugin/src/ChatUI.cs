// ChatUI.cs - Chat Interface Window
using System;
using System.Windows.Forms;
using System.Threading.Tasks;

namespace CADCopilot
{
    public class ChatUI : Form
    {
        private TextBox messageHistory;
        private TextBox commandInput;
        private Button sendButton;
        private APIClient apiClient;
        
        public ChatUI(APIClient client)
        {
            apiClient = client;
            InitializeComponents();
        }
        
        private void InitializeComponents()
        {
            // Window properties
            this.Text = "CAD AI Copilot";
            this.Width = 400;
            this.Height = 600;
            this.StartPosition = FormStartPosition.CenterScreen;
            
            // Message history (read-only)
            messageHistory = new TextBox();
            messageHistory.Multiline = true;
            messageHistory.ReadOnly = true;
            messageHistory.Dock = DockStyle.Fill;
            messageHistory.Width = 380;
            messageHistory.Height = 500;
            
            // Command input
            commandInput = new TextBox();
            commandInput.Multiline = false;
            commandInput.Height = 30;
            commandInput.Dock = DockStyle.Bottom;
            commandInput.Width = 380;
            
            // Send button
            sendButton = new Button();
            sendButton.Text = "Send";
            sendButton.Width = 80;
            sendButton.Height = 30;
            sendButton.Dock = DockStyle.Bottom;
            sendButton.Click += SendButton_Click;
            
            // Add controls
            this.Controls.Add(messageHistory);
            this.Controls.Add(commandInput);
            this.Controls.Add(sendButton);
        }
        
        private async void SendButton_Click(object sender, EventArgs e)
        {
            string command = commandInput.Text.Trim();
            
            if (string.IsNullOrEmpty(command))
                return;
            
            try
            {
                // Add to history
                AddMessage("You: " + command);
                
                // Send to API
                string response = await apiClient.ExecuteCommand(command);
                
                // Add response
                AddMessage("AI: " + response);
                
                // Clear input
                commandInput.Text = "";
            }
            catch (Exception ex)
            {
                AddMessage("Error: " + ex.Message);
            }
        }
        
        private void AddMessage(string message)
        {
            messageHistory.AppendText(message + Environment.NewLine);
        }
    }
}
