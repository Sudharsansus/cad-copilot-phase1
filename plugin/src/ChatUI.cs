// ChatUI.cs - VS Code Copilot Style Chat Panel (Fixed Layout v2)
using System;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Windows.Forms;
using System.IO;

namespace CADCopilot
{
    public class ChatUI : Form
    {
        // Controls
        private Panel headerPanel;
        private Panel buttonsPanel;
        private Panel messagesPanel;
        private Panel inputPanel;
        private FlowLayoutPanel messageFlow;
        private TextBox commandInput;
        private Button sendButton;
        private Button uploadDwgButton;
        private Button uploadExcelButton;
        private Button autoDrawButton;
        private Button downloadButton;
        private Label statusLabel;
        private Timer typingTimer;
        private int typingDots = 0;

        // State
        private APIClient apiClient;
        private AutoCADDrawing cadDrawing = null;
        private string currentFileId   = null;
        private string currentExcelId  = null;
        private string currentOutputId = null;

        // VS Code Colors
        private readonly Color VS_BG       = Color.FromArgb(30, 30, 30);
        private readonly Color VS_PANEL    = Color.FromArgb(37, 37, 38);
        private readonly Color VS_BORDER   = Color.FromArgb(68, 68, 68);
        private readonly Color VS_INPUT_BG = Color.FromArgb(58, 58, 58);
        private readonly Color VS_TEXT     = Color.FromArgb(204, 204, 204);
        private readonly Color VS_BLUE     = Color.FromArgb(0, 122, 204);
        private readonly Color VS_GREEN    = Color.FromArgb(78, 201, 176);
        private readonly Color VS_RED      = Color.FromArgb(244, 135, 113);
        private readonly Color VS_YELLOW   = Color.FromArgb(220, 220, 170);
        private readonly Color VS_GRAY     = Color.FromArgb(110, 110, 110);
        private readonly Color AI_BUBBLE   = Color.FromArgb(45, 45, 48);
        private readonly Color USER_BUBBLE = Color.FromArgb(0, 90, 158);

        public ChatUI(APIClient client)
        {
            apiClient = client;
            this.DoubleBuffered = true;
            SetupTypingTimer();
            BuildUI();
            // Set messageFlow width after layout is complete
            this.Load += (s, e) =>
            {
                UpdateFlowWidth();
                AddBubble("system",
                    "Welcome to CAD AI Copilot!\n\n" +
                    "Upload your DWG base map and Excel LPS Book to auto-draw " +
                    "transmission line corridors, tower markers and land parcel labels.");
            };
        }

        // ─────────────────────────────────────────────
        //  TIMER
        // ─────────────────────────────────────────────
        private void SetupTypingTimer()
        {
            typingTimer = new Timer { Interval = 450 };
            typingTimer.Tick += (s, e) =>
            {
                typingDots = (typingDots + 1) % 4;
                SafeSet(() =>
                {
                    statusLabel.Text      = "AI is thinking" + new string('.', typingDots);
                    statusLabel.ForeColor = VS_GREEN;
                });
            };
        }

        // ─────────────────────────────────────────────
        //  BUILD UI
        // ─────────────────────────────────────────────
        private void BuildUI()
        {
            // ── FORM ──────────────────────────────────
            this.Text            = "CAD AI Copilot";
            this.Size            = new Size(430, 720);
            this.MinimumSize     = new Size(380, 500);
            this.BackColor       = VS_BG;
            this.ForeColor       = VS_TEXT;
            this.Font            = new Font("Segoe UI", 9f);
            this.FormBorderStyle = FormBorderStyle.SizableToolWindow;
            this.StartPosition   = FormStartPosition.Manual;
            this.Location        = new Point(
                Screen.PrimaryScreen.WorkingArea.Width - 445, 60);

            // ── HEADER ────────────────────────────────
            headerPanel = new Panel
            {
                Dock      = DockStyle.Top,
                Height    = 46,
                BackColor = Color.FromArgb(31, 31, 31)
            };

            var iconLbl = new Label
            {
                Text      = "⚡",
                Font      = new Font("Segoe UI", 13f),
                ForeColor = VS_BLUE,
                Location  = new Point(12, 10),
                AutoSize  = true
            };
            var titleLbl = new Label
            {
                Text      = "CAD AI Copilot",
                Font      = new Font("Segoe UI", 10f, FontStyle.Bold),
                ForeColor = VS_TEXT,
                Location  = new Point(34, 12),
                AutoSize  = true
            };
            var betaLbl = new Label
            {
                Text      = "beta",
                Font      = new Font("Segoe UI", 7f),
                ForeColor = VS_GRAY,
                Location  = new Point(155, 15),
                AutoSize  = true
            };
            // Green online dot (owner-drawn circle)
            var dot = new Panel
            {
                Size      = new Size(10, 10),
                BackColor = Color.Transparent,
                Location  = new Point(395, 18)
            };
            dot.Paint += (s, e) =>
            {
                e.Graphics.SmoothingMode = SmoothingMode.AntiAlias;
                using var br = new SolidBrush(VS_GREEN);
                e.Graphics.FillEllipse(br, 0, 0, 9, 9);
            };

            headerPanel.Controls.AddRange(new Control[] { iconLbl, titleLbl, betaLbl, dot });
            headerPanel.Paint += (s, e) =>
            {
                using var p = new Pen(VS_BORDER);
                e.Graphics.DrawLine(p, 0, headerPanel.Height - 1,
                    headerPanel.Width, headerPanel.Height - 1);
            };

            // ── BUTTONS PANEL ─────────────────────────
            // Layout: 10 pad + 32 row1 + 6 gap + 32 row2 + 6 gap + 16 status + 8 pad = 110
            buttonsPanel = new Panel
            {
                Dock      = DockStyle.Top,
                Height    = 110,
                BackColor = VS_PANEL
            };

            // Responsive column widths (48% each, 2% gap, 2% left pad)
            // We'll use fixed values sized for 430px form
            int bW = 192; int bH = 32;
            int col1 = 10; int col2 = 212;
            int row1Y = 10; int row2Y = 50;

            uploadDwgButton   = MakeBtn("📁  Upload DWG",    col1, row1Y, bW, bH, VS_BLUE);
            uploadExcelButton = MakeBtn("📊  Upload Excel",   col2, row1Y, bW, bH, VS_BLUE);
            autoDrawButton    = MakeBtn("🤖  Auto Draw LPS",  col1, row2Y, bW, bH,
                                        Color.FromArgb(55, 55, 55));
            downloadButton    = MakeBtn("⬇  Download DWG",   col2, row2Y, bW, bH,
                                        Color.FromArgb(55, 55, 55));
            autoDrawButton.Enabled = false;
            downloadButton.Enabled = false;

            uploadDwgButton.Click   += UploadDwg_Click;
            uploadExcelButton.Click += UploadExcel_Click;
            autoDrawButton.Click    += AutoDraw_Click;
            downloadButton.Click    += Download_Click;

            statusLabel = new Label
            {
                Text      = "Upload DWG and Excel LPS Book to start",
                ForeColor = VS_GRAY,
                Font      = new Font("Segoe UI", 7.5f),
                Location  = new Point(col1, 90),
                Size      = new Size(400, 14),
                BackColor = Color.Transparent
            };

            buttonsPanel.Controls.AddRange(new Control[]
            {
                uploadDwgButton, uploadExcelButton,
                autoDrawButton, downloadButton, statusLabel
            });
            buttonsPanel.Paint += (s, e) =>
            {
                using var p = new Pen(VS_BORDER);
                e.Graphics.DrawLine(p, 0, buttonsPanel.Height - 1,
                    buttonsPanel.Width, buttonsPanel.Height - 1);
            };

            // ── INPUT PANEL ───────────────────────────
            // 10 top pad + 36 input + 10 bottom = 56
            inputPanel = new Panel
            {
                Dock      = DockStyle.Bottom,
                Height    = 56,
                BackColor = VS_PANEL
            };
            inputPanel.Paint += (s, e) =>
            {
                using var p = new Pen(VS_BORDER);
                e.Graphics.DrawLine(p, 0, 0, inputPanel.Width, 0);
            };
            inputPanel.Resize += (s, e) => LayoutInputPanel();

            // Wrapper gives the textbox a visible border
            var inputWrap = new Panel
            {
                Tag       = "inputWrap",
                Location  = new Point(10, 10),
                Size      = new Size(10, 36), // width set in LayoutInputPanel
                BackColor = VS_INPUT_BG
            };
            inputWrap.Paint += (s, e) =>
            {
                ControlPaint.DrawBorder(e.Graphics, inputWrap.ClientRectangle,
                    Color.FromArgb(85, 85, 85), ButtonBorderStyle.Solid);
            };

            commandInput = new TextBox
            {
                Location    = new Point(8, 7),
                Width       = 10, // set in LayoutInputPanel
                BackColor   = VS_INPUT_BG,
                ForeColor   = VS_TEXT,
                BorderStyle = BorderStyle.None,
                Font        = new Font("Cascadia Code", 9f)
            };
            commandInput.KeyDown += (s, e) =>
            {
                if (e.KeyCode == Keys.Enter && !e.Shift)
                {
                    SendButton_Click(s, e);
                    e.Handled         = true;
                    e.SuppressKeyPress = true;
                }
            };
            inputWrap.Controls.Add(commandInput);

            sendButton = new Button
            {
                Tag       = "sendBtn",
                Text      = "Send",
                Location  = new Point(10, 10), // x set in LayoutInputPanel
                Size      = new Size(70, 36),
                BackColor = VS_BLUE,
                ForeColor = Color.White,
                FlatStyle = FlatStyle.Flat,
                Font      = new Font("Segoe UI", 9f, FontStyle.Bold),
                Cursor    = Cursors.Hand
            };
            sendButton.FlatAppearance.BorderSize = 0;
            sendButton.Click += SendButton_Click;

            inputPanel.Controls.AddRange(new Control[] { inputWrap, sendButton });

            // ── MESSAGES AREA ─────────────────────────
            messagesPanel = new Panel
            {
                Dock       = DockStyle.Fill,
                BackColor  = VS_BG,
                AutoScroll = true
            };

            // FlowLayoutPanel: NO Dock — width is managed manually so AutoSize
            // can grow it downward and messagesPanel can scroll it.
            messageFlow = new FlowLayoutPanel
            {
                FlowDirection  = FlowDirection.TopDown,
                WrapContents   = false,
                AutoSize       = true,
                AutoSizeMode   = AutoSizeMode.GrowAndShrink,
                BackColor      = VS_BG,
                Location       = new Point(0, 0),
                Padding        = new Padding(6, 6, 6, 6)
            };
            messagesPanel.Controls.Add(messageFlow);

            // ── ASSEMBLE ──────────────────────────────
            // Controls added in reverse dock priority:
            //   Fill first, then Bottom, then Top items (last Top added = outermost top)
            this.Controls.Add(messagesPanel);   // Fill
            this.Controls.Add(inputPanel);      // Bottom
            this.Controls.Add(buttonsPanel);    // Top (inner)
            this.Controls.Add(headerPanel);     // Top (outermost)
        }

        // ─────────────────────────────────────────────
        //  LAYOUT HELPERS
        // ─────────────────────────────────────────────
        private void UpdateFlowWidth()
        {
            if (messagesPanel == null || messageFlow == null) return;
            int w = messagesPanel.ClientSize.Width;
            if (w < 100) w = 380;
            messageFlow.Width = w;
        }

        private void LayoutInputPanel()
        {
            if (inputPanel == null) return;
            int clientW = inputPanel.ClientSize.Width;
            int sendW   = 70;
            int gap     = 6;
            int leftPad = 10;
            int rightPad = 10;

            int wrapW = clientW - leftPad - gap - sendW - rightPad;
            if (wrapW < 80) wrapW = 80;

            // Find controls by tag
            foreach (Control c in inputPanel.Controls)
            {
                if (c.Tag?.ToString() == "inputWrap")
                {
                    c.Width = wrapW;
                    // Resize inner textbox too
                    foreach (Control inner in c.Controls)
                        if (inner is TextBox tb)
                            tb.Width = wrapW - 16; // leave 8px padding each side
                }
                if (c.Tag?.ToString() == "sendBtn")
                    c.Location = new Point(leftPad + wrapW + gap, 10);
            }
        }

        // ─────────────────────────────────────────────
        //  ADD MESSAGE BUBBLE
        // ─────────────────────────────────────────────
        private void AddBubble(string type, string text)
        {
            if (messageFlow.InvokeRequired)
            {
                messageFlow.Invoke(new Action(() => AddBubble(type, text)));
                return;
            }

            bool isUser   = type == "user";
            bool isError  = type == "error";
            bool isSystem = type == "system";

            // Colors
            Color avBg      = isUser ? VS_BLUE : isError ? VS_RED : VS_GREEN;
            Color bubbleBg  = isUser   ? USER_BUBBLE
                            : isError  ? Color.FromArgb(75, 28, 28)
                            : isSystem ? Color.FromArgb(42, 42, 44)
                            : AI_BUBBLE;
            Color textColor = isError ? Color.FromArgb(255, 160, 140) : VS_TEXT;
            string avTxt    = isUser ? "U" : isError ? "!" : "AI";

            // Available width for this row
            int panelW = messageFlow.Width - 12;
            if (panelW < 200) panelW = 370;

            // ── Measure text height properly ──────────
            // Max bubble width = panelW minus avatar(30) + avatar-gap(8) + right-margin(10)
            int maxBubW = panelW - 52;
            if (maxBubW < 80) maxBubW = 200;
            var msgFont = new Font("Segoe UI", 9f);
            // Inner text area width (bubble padding = 10px each side)
            int textAreaW = maxBubW - 20;
            var textSize  = TextRenderer.MeasureText(
                text, msgFont,
                new Size(textAreaW, int.MaxValue),
                TextFormatFlags.WordBreak | TextFormatFlags.TextBoxControl);
            int bubW  = Math.Min(textSize.Width  + 22, maxBubW);
            int bubH  = textSize.Height + 18;    // +18 = top(8) + bottom(8) + fudge(2)
            int rowH  = bubH + 22;               // +22 = timestamp line(14) + gaps(8)

            // ── Row container ─────────────────────────
            var row = new Panel
            {
                Width     = panelW,
                Height    = rowH,
                BackColor = VS_BG,
                Margin    = new Padding(0, 0, 0, 4)
            };

            // ── Avatar ────────────────────────────────
            Color avBgCopy  = avBg;
            string avTxtCopy = avTxt;
            var avatar = new Panel
            {
                Size      = new Size(30, 30),
                BackColor = Color.Transparent
            };
            avatar.Paint += (s, e) =>
            {
                var g = e.Graphics;
                g.SmoothingMode = SmoothingMode.AntiAlias;
                using var br = new SolidBrush(avBgCopy);
                g.FillEllipse(br, 1, 1, 27, 27);
                var f = new Font("Segoe UI",
                    avTxtCopy.Length > 1 ? 7f : 9f, FontStyle.Bold);
                var sz = g.MeasureString(avTxtCopy, f);
                g.DrawString(avTxtCopy, f, Brushes.White,
                    (29f - sz.Width) / 2f, (29f - sz.Height) / 2f);
            };

            // ── Bubble label ──────────────────────────
            var msgLbl = new Label
            {
                Text        = text,
                Font        = msgFont,
                ForeColor   = textColor,
                BackColor   = bubbleBg,
                Size        = new Size(bubW, bubH),
                Padding     = new Padding(10, 8, 10, 8),
                AutoSize    = false   // size is computed above
            };

            // ── Timestamp ─────────────────────────────
            var tsLbl = new Label
            {
                Text      = DateTime.Now.ToString("HH:mm"),
                Font      = new Font("Segoe UI", 7f),
                ForeColor = VS_GRAY,
                AutoSize  = true,
                BackColor = Color.Transparent
            };

            // ── Position controls ─────────────────────
            int avatarTop = 2;
            int bubbleTop = 2;

            if (isUser)
            {
                // User: avatar on the right, bubble to its left
                int avatarLeft = panelW - 34;
                int bubbleLeft = avatarLeft - bubW - 6;
                if (bubbleLeft < 0) bubbleLeft = 0;
                avatar.Location = new Point(avatarLeft, avatarTop);
                msgLbl.Location = new Point(bubbleLeft, bubbleTop);
                tsLbl.Location  = new Point(bubbleLeft, bubbleTop + bubH + 3);
            }
            else
            {
                // AI / System: avatar on the left, bubble to its right
                avatar.Location = new Point(4, avatarTop);
                msgLbl.Location = new Point(38, bubbleTop);
                tsLbl.Location  = new Point(38, bubbleTop + bubH + 3);
            }

            row.Controls.AddRange(new Control[] { avatar, msgLbl, tsLbl });
            messageFlow.Controls.Add(row);

            // Scroll to bottom
            messagesPanel.AutoScrollPosition =
                new Point(0, messageFlow.Height + 200);
        }

        // ─────────────────────────────────────────────
        //  TYPING INDICATOR
        // ─────────────────────────────────────────────
        private void ShowTyping(bool show)
        {
            SafeSet(() =>
            {
                if (show)
                {
                    typingDots = 0;
                    statusLabel.Text      = "AI is thinking...";
                    statusLabel.ForeColor = VS_GREEN;
                    typingTimer.Start();
                    sendButton.Enabled    = false;
                }
                else
                {
                    typingTimer.Stop();
                    statusLabel.Text   = "";
                    sendButton.Enabled = true;
                }
            });
        }

        // ─────────────────────────────────────────────
        //  BUTTON HANDLERS
        // ─────────────────────────────────────────────
        private async void UploadDwg_Click(object sender, EventArgs e)
        {
            try
            {
                using var dlg = new OpenFileDialog
                { Filter = "DWG Files|*.dwg", Title = "Select DWG Base Map" };
                if (dlg.ShowDialog() != DialogResult.OK) return;

                uploadDwgButton.Enabled = false;
                uploadDwgButton.Text    = "⏳  Uploading...";
                SetStatus("Uploading DWG...", VS_YELLOW);

                currentFileId = await apiClient.UploadDwg(dlg.FileName);

                if (currentFileId != null)
                {
                    uploadDwgButton.Text     = "✅  DWG Ready";
                    uploadDwgButton.BackColor = Color.FromArgb(28, 68, 28);
                    AddBubble("system", "DWG uploaded: " + Path.GetFileName(dlg.FileName));
                    CheckReady();
                }
                else
                {
                    AddBubble("error", "DWG upload failed. Check your internet connection.");
                    uploadDwgButton.Text      = "📁  Upload DWG";
                    uploadDwgButton.BackColor  = VS_BLUE;
                    uploadDwgButton.Enabled    = true;
                }
                SetStatus("", VS_GRAY);
            }
            catch (System.Exception ex)
            {
                AddBubble("error", "Upload error: " + ex.Message);
                uploadDwgButton.Text     = "📁  Upload DWG";
                uploadDwgButton.BackColor = VS_BLUE;
                uploadDwgButton.Enabled   = true;
                SetStatus("", VS_GRAY);
            }
        }

        private async void UploadExcel_Click(object sender, EventArgs e)
        {
            try
            {
                using var dlg = new OpenFileDialog
                { Filter = "Excel Files|*.xlsx;*.xls", Title = "Select LPS Book" };
                if (dlg.ShowDialog() != DialogResult.OK) return;

                uploadExcelButton.Enabled = false;
                uploadExcelButton.Text    = "⏳  Uploading...";
                SetStatus("Uploading LPS Book...", VS_YELLOW);

                currentExcelId = await apiClient.UploadExcel(dlg.FileName);

                if (currentExcelId != null)
                {
                    uploadExcelButton.Text     = "✅  Excel Ready";
                    uploadExcelButton.BackColor = Color.FromArgb(28, 68, 28);
                    AddBubble("system", "LPS Book uploaded: " + Path.GetFileName(dlg.FileName));
                    CheckReady();
                }
                else
                {
                    AddBubble("error", "Excel upload failed. Check your connection.");
                    uploadExcelButton.Text     = "📊  Upload Excel";
                    uploadExcelButton.BackColor = VS_BLUE;
                    uploadExcelButton.Enabled   = true;
                }
                SetStatus("", VS_GRAY);
            }
            catch (System.Exception ex)
            {
                AddBubble("error", "Upload error: " + ex.Message);
                uploadExcelButton.Text     = "📊  Upload Excel";
                uploadExcelButton.BackColor = VS_BLUE;
                uploadExcelButton.Enabled   = true;
                SetStatus("", VS_GRAY);
            }
        }

        private async void AutoDraw_Click(object sender, EventArgs e)
        {
            try
            {
                autoDrawButton.Enabled = false;
                autoDrawButton.Text    = "⏳  Drawing...";
                ShowTyping(true);
                AddBubble("ai",
                    "Starting auto-draw...\n" +
                    "This may take 30–60 seconds on first run (server wake-up time).");

                var (outputId, parcels) = await apiClient.AutoDraw(currentFileId, currentExcelId);
                ShowTyping(false);

                if (outputId != null)
                {
                    currentOutputId            = outputId;
                    downloadButton.Enabled     = true;
                    downloadButton.BackColor   = VS_BLUE;
                    autoDrawButton.Text        = "✅  Done";
                    AddBubble("ai",
                        "Done! Drew " + parcels + " land parcels.\n\n" +
                        "Layers created:\n" +
                        "• LPS_CORRIDOR — corridor strips\n" +
                        "• LPS_TOWER — tower markers\n" +
                        "• LPS_INFOBOX — SF info boxes\n" +
                        "• N/S/E/W boundary labels\n\n" +
                        "Click Download DWG to save your file.");
                }
                else
                {
                    AddBubble("error",
                        "Auto-draw failed.\nCheck Render backend logs at dashboard.render.com");
                    autoDrawButton.Text      = "🤖  Auto Draw LPS";
                    autoDrawButton.BackColor = VS_GREEN;
                    autoDrawButton.ForeColor = Color.Black;
                    autoDrawButton.Enabled   = true;
                }
            }
            catch (System.Exception ex)
            {
                ShowTyping(false);
                AddBubble("error", "Auto-draw error: " + ex.Message);
                autoDrawButton.Text    = "🤖  Auto Draw LPS";
                autoDrawButton.Enabled = true;
            }
        }

        private async void Download_Click(object sender, EventArgs e)
        {
            try
            {
                using var dlg = new SaveFileDialog
                {
                    Filter   = "DWG Files|*.dwg",
                    FileName = "lps_output_" + DateTime.Now.ToString("yyyyMMdd_HHmm") + ".dwg",
                    Title    = "Save Output DWG"
                };
                if (dlg.ShowDialog() != DialogResult.OK) return;

                SetStatus("Downloading DWG...", VS_YELLOW);
                string saved = await apiClient.DownloadOutput(currentOutputId, dlg.FileName);

                AddBubble(saved != null ? "system" : "error",
                    saved != null ? "Saved to:\n" + saved : "Download failed. Try again.");
                SetStatus("", VS_GRAY);
            }
            catch (System.Exception ex)
            {
                AddBubble("error", "Download error: " + ex.Message);
                SetStatus("", VS_GRAY);
            }
        }

        private async void SendButton_Click(object sender, EventArgs e)
        {
            try
            {
                string cmd = commandInput.Text.Trim();
                if (string.IsNullOrEmpty(cmd)) return;
                if (currentFileId == null)
                {
                    AddBubble("error", "Please upload a DWG file first.");
                    return;
                }

                commandInput.Text = "";
                AddBubble("user", cmd);
                ShowTyping(true);

                string response = await apiClient.ExecuteCommand(currentFileId, cmd);
                ShowTyping(false);

                if (response != null)
                {
                    AddBubble("ai", response);
                    try
                    {
                        if (cadDrawing == null) cadDrawing = new AutoCADDrawing();
                        cadDrawing.DrawFromApiResponse(response);
                    }
                    catch { /* drawing errors should not crash the UI */ }
                }
                else
                    AddBubble("error", "Command failed. Please try again.");
            }
            catch (System.Exception ex)
            {
                ShowTyping(false);
                AddBubble("error", "Error: " + ex.Message);
                sendButton.Enabled = true;
            }
        }

        // ─────────────────────────────────────────────
        //  HELPERS
        // ─────────────────────────────────────────────
        private void CheckReady()
        {
            if (currentFileId != null && currentExcelId != null)
            {
                autoDrawButton.Enabled   = true;
                autoDrawButton.BackColor = VS_GREEN;
                autoDrawButton.ForeColor = Color.Black;
                autoDrawButton.Text      = "🤖  Auto Draw LPS";
                AddBubble("system",
                    "Both files ready!\n" +
                    "Click Auto Draw LPS to generate the transmission line layout.");
            }
        }

        private void SetStatus(string text, Color color)
        {
            SafeSet(() => { statusLabel.Text = text; statusLabel.ForeColor = color; });
        }

        private void SafeSet(Action action)
        {
            if (statusLabel == null) return;
            if (statusLabel.InvokeRequired)
                statusLabel.Invoke(action);
            else
                action();
        }

        private Button MakeBtn(string text, int x, int y, int w, int h, Color bg)
        {
            var b = new Button
            {
                Text        = text,
                Location    = new Point(x, y),
                Size        = new Size(w, h),
                BackColor   = bg,
                ForeColor   = Color.White,
                FlatStyle   = FlatStyle.Flat,
                Font        = new Font("Segoe UI", 8.5f),
                Cursor      = Cursors.Hand,
                TextAlign   = ContentAlignment.MiddleLeft,
                Padding     = new Padding(8, 0, 0, 0)
            };
            b.FlatAppearance.BorderSize = 0;
            return b;
        }

        // ─────────────────────────────────────────────
        //  RESIZE
        // ─────────────────────────────────────────────
        protected override void OnResize(EventArgs e)
        {
            base.OnResize(e);
            UpdateFlowWidth();
        }

        protected override void OnFormClosing(FormClosingEventArgs e)
        {
            typingTimer?.Stop();
            typingTimer?.Dispose();
            base.OnFormClosing(e);
        }
    }
}