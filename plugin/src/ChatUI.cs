using System;
using System.Drawing;
using System.Windows.Forms;
using System.Threading.Tasks;
using System.IO;

namespace CADCopilot
{
    public class ChatUI : Form
    {
        private RichTextBox messageHistory;
        private TextBox commandInput;
        private Button sendButton;
        private Button uploadDwgButton;
        private Button uploadExcelButton;
        private Button autoDrawButton;
        private Button downloadButton;
        private Label statusLabel;
        private Panel topPanel;
        private Panel bottomPanel;
        private APIClient apiClient;
        private AutoCADDrawing cadDrawing = null;
        private string currentFileId = null;
        private string currentExcelId = null;
        private string currentOutputId = null;

        private readonly Color BG_DARK = Color.FromArgb(30, 30, 30);
        private readonly Color BG_PANEL = Color.FromArgb(37, 37, 38);
        private readonly Color BG_INPUT = Color.FromArgb(60, 60, 60);
        private readonly Color TEXT_WHITE = Color.FromArgb(212, 212, 212);
        private readonly Color ACCENT_BLUE = Color.FromArgb(0, 122, 204);
        private readonly Color ACCENT_GREEN = Color.FromArgb(78, 201, 176);

        public ChatUI(APIClient client)
        {
            apiClient = client;
            // cadDrawing initialized lazily — NOT here, avoids crash on load
            InitializeComponents();
        }

        private void InitializeComponents()
        {
            this.Text = "CAD AI Copilot";
            this.Width = 420;
            this.Height = 700;
            this.MinimumSize = new Size(380, 500);
            this.BackColor = BG_DARK;
            this.ForeColor = TEXT_WHITE;
            this.StartPosition = FormStartPosition.Manual;
            this.Location = new Point(Screen.PrimaryScreen.WorkingArea.Width - 440, 100);
            this.Font = new Font("Segoe UI", 9f);

            topPanel = new Panel
            {
                Dock = DockStyle.Top,
                Height = 110,
                BackColor = BG_PANEL,
                Padding = new Padding(8)
            };

            var titleLabel = new Label
            {
                Text = "CAD AI Copilot",
                ForeColor = ACCENT_BLUE,
                Font = new Font("Segoe UI", 11f, FontStyle.Bold),
                Location = new Point(8, 8),
                AutoSize = true
            };

            uploadDwgButton = CreateButton("Upload DWG", 8, 35, ACCENT_BLUE);
            uploadDwgButton.Click += UploadDwg_Click;

            uploadExcelButton = CreateButton("Upload Excel", 210, 35, ACCENT_BLUE);
            uploadExcelButton.Click += UploadExcel_Click;

            autoDrawButton = CreateButton("Auto Draw LPS", 8, 70, ACCENT_GREEN);
            autoDrawButton.Width = 190;
            autoDrawButton.Enabled = false;
            autoDrawButton.Click += AutoDraw_Click;

            downloadButton = CreateButton("Download DWG", 210, 70, Color.FromArgb(100, 100, 100));
            downloadButton.Enabled = false;
            downloadButton.Click += Download_Click;

            topPanel.Controls.AddRange(new Control[] {
                titleLabel, uploadDwgButton, uploadExcelButton, autoDrawButton, downloadButton
            });

            messageHistory = new RichTextBox
            {
                Dock = DockStyle.Fill,
                ReadOnly = true,
                BackColor = BG_DARK,
                ForeColor = TEXT_WHITE,
                BorderStyle = BorderStyle.None,
                Font = new Font("Segoe UI", 9.5f),
                Padding = new Padding(8),
                ScrollBars = RichTextBoxScrollBars.Vertical
            };

            bottomPanel = new Panel
            {
                Dock = DockStyle.Bottom,
                Height = 80,
                BackColor = BG_PANEL,
                Padding = new Padding(8)
            };

            statusLabel = new Label
            {
                Text = "Upload DWG and Excel to start",
                ForeColor = Color.Gray,
                Location = new Point(8, 5),
                AutoSize = true,
                Font = new Font("Segoe UI", 8f)
            };

            commandInput = new TextBox
            {
                Location = new Point(8, 25),
                Width = 310,
                Height = 36,
                BackColor = BG_INPUT,
                ForeColor = TEXT_WHITE,
                BorderStyle = BorderStyle.FixedSingle,
                Font = new Font("Segoe UI", 10f)
            };
            commandInput.KeyDown += (s, e) =>
            {
                if (e.KeyCode == Keys.Enter) { SendButton_Click(s, e); e.Handled = true; }
            };

            sendButton = new Button
            {
                Text = "Send",
                Location = new Point(325, 25),
                Width = 75,
                Height = 36,
                BackColor = ACCENT_BLUE,
                ForeColor = Color.White,
                FlatStyle = FlatStyle.Flat,
                Font = new Font("Segoe UI", 9f, FontStyle.Bold),
                Cursor = Cursors.Hand
            };
            sendButton.FlatAppearance.BorderSize = 0;
            sendButton.Click += SendButton_Click;

            bottomPanel.Controls.AddRange(new Control[] { statusLabel, commandInput, sendButton });

            this.Controls.Add(messageHistory);
            this.Controls.Add(topPanel);
            this.Controls.Add(bottomPanel);

            AddMessage("system", "Welcome to CAD AI Copilot! Upload your DWG and Excel files to begin.");
        }

        private async void UploadDwg_Click(object sender, EventArgs e)
        {
            try
            {
                using var dialog = new OpenFileDialog { Filter = "DWG Files|*.dwg", Title = "Select DWG File" };
                if (dialog.ShowDialog() != DialogResult.OK) return;
                SetStatus("Uploading DWG...");
                uploadDwgButton.Enabled = false;
                currentFileId = await apiClient.UploadDwg(dialog.FileName);
                if (currentFileId != null)
                {
                    uploadDwgButton.Text = "DWG Uploaded";
                    AddMessage("system", "DWG uploaded successfully.");
                    CheckAutoDrawReady();
                }
                else
                {
                    AddMessage("error", "DWG upload failed. Check your connection.");
                    uploadDwgButton.Enabled = true;
                }
                SetStatus("");
            }
            catch (System.Exception ex)
            {
                AddMessage("error", $"DWG upload error: {ex.Message}");
                uploadDwgButton.Enabled = true;
                SetStatus("");
            }
        }

        private async void UploadExcel_Click(object sender, EventArgs e)
        {
            try
            {
                using var dialog = new OpenFileDialog { Filter = "Excel Files|*.xlsx;*.xls", Title = "Select Excel LPS File" };
                if (dialog.ShowDialog() != DialogResult.OK) return;
                SetStatus("Uploading Excel...");
                uploadExcelButton.Enabled = false;
                currentExcelId = await apiClient.UploadExcel(dialog.FileName);
                if (currentExcelId != null)
                {
                    uploadExcelButton.Text = "Excel Uploaded";
                    AddMessage("system", "Excel LPS file uploaded successfully.");
                    CheckAutoDrawReady();
                }
                else
                {
                    AddMessage("error", "Excel upload failed. Check your connection.");
                    uploadExcelButton.Enabled = true;
                }
                SetStatus("");
            }
            catch (System.Exception ex)
            {
                AddMessage("error", $"Excel upload error: {ex.Message}");
                uploadExcelButton.Enabled = true;
                SetStatus("");
            }
        }

        private async void AutoDraw_Click(object sender, EventArgs e)
        {
            try
            {
                SetStatus("AI is drawing transmission lines...");
                autoDrawButton.Enabled = false;
                AddMessage("ai", "Starting auto-draw... This may take a moment.");
                var (outputId, parcels) = await apiClient.AutoDraw(currentFileId, currentExcelId);
                if (outputId != null)
                {
                    currentOutputId = outputId;
                    downloadButton.Enabled = true;
                    downloadButton.BackColor = ACCENT_GREEN;
                    AddMessage("ai", $"Done! Drew {parcels} land parcels. Click Download DWG to get your file.");
                }
                else
                {
                    AddMessage("error", "Auto-draw failed. Please try again.");
                    autoDrawButton.Enabled = true;
                }
                SetStatus("");
            }
            catch (System.Exception ex)
            {
                AddMessage("error", $"Auto-draw error: {ex.Message}");
                autoDrawButton.Enabled = true;
                SetStatus("");
            }
        }

        private async void Download_Click(object sender, EventArgs e)
        {
            try
            {
                using var dialog = new SaveFileDialog { Filter = "DWG Files|*.dwg", FileName = "lps_output.dwg" };
                if (dialog.ShowDialog() != DialogResult.OK) return;
                SetStatus("Downloading...");
                string saved = await apiClient.DownloadOutput(currentOutputId, dialog.FileName);
                if (saved != null)
                    AddMessage("system", $"File saved to: {saved}");
                else
                    AddMessage("error", "Download failed.");
                SetStatus("");
            }
            catch (System.Exception ex)
            {
                AddMessage("error", $"Download error: {ex.Message}");
                SetStatus("");
            }
        }

        private async void SendButton_Click(object sender, EventArgs e)
        {
            try
            {
                string command = commandInput.Text.Trim();
                if (string.IsNullOrEmpty(command)) return;
                if (currentFileId == null) { AddMessage("error", "Please upload a DWG file first."); return; }
                commandInput.Text = "";
                AddMessage("user", command);
                SetStatus("AI thinking...");
                sendButton.Enabled = false;
                string response = await apiClient.ExecuteCommand(currentFileId, command);
                if (response != null)
                {
                    AddMessage("ai", response);
                    try
                    {
                        if (cadDrawing == null) cadDrawing = new AutoCADDrawing();
                        cadDrawing.DrawFromApiResponse(response);
                    }
                    catch { }
                }
                else
                {
                    AddMessage("error", "Command failed. Try again.");
                }
                sendButton.Enabled = true;
                SetStatus("");
            }
            catch (System.Exception ex)
            {
                AddMessage("error", $"Command error: {ex.Message}");
                sendButton.Enabled = true;
                SetStatus("");
            }
        }

        private void CheckAutoDrawReady()
        {
            if (currentFileId != null && currentExcelId != null)
            {
                autoDrawButton.Enabled = true;
                autoDrawButton.BackColor = ACCENT_GREEN;
                AddMessage("system", "Both files ready! Click Auto Draw LPS to start.");
            }
        }

        private void AddMessage(string type, string message)
        {
            if (messageHistory.InvokeRequired)
            {
                messageHistory.Invoke(new Action(() => AddMessage(type, message)));
                return;
            }
            Color color = type switch
            {
                "user" => Color.FromArgb(100, 180, 255),
                "ai" => ACCENT_GREEN,
                "error" => Color.FromArgb(255, 100, 100),
                _ => Color.Gray
            };
            string prefix = type switch
            {
                "user" => "You",
                "ai" => "AI",
                "error" => "Error",
                _ => "System"
            };
            messageHistory.SelectionColor = color;
            messageHistory.AppendText($"{prefix}: {message}{Environment.NewLine}{Environment.NewLine}");
            messageHistory.ScrollToCaret();
        }

        private void SetStatus(string text)
        {
            if (statusLabel.InvokeRequired)
                statusLabel.Invoke(new Action(() => statusLabel.Text = text));
            else
                statusLabel.Text = text;
        }

        private Button CreateButton(string text, int x, int y, Color backColor)
        {
            return new Button
            {
                Text = text,
                Location = new Point(x, y),
                Width = 190,
                Height = 28,
                BackColor = backColor,
                ForeColor = Color.White,
                FlatStyle = FlatStyle.Flat,
                Font = new Font("Segoe UI", 8.5f),
                Cursor = Cursors.Hand,
                FlatAppearance = { BorderSize = 0 }
            };
        }
    }
}