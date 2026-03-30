// APIClient.cs - API Communication
using System;
using System.Net.Http;
using System.Threading.Tasks;
using System.Text.Json;
using System.Text;

namespace CADCopilot
{
    public class APIClient
    {
        private string baseUrl;
        private HttpClient httpClient;
        
        public APIClient(string url)
        {
            baseUrl = url;
            httpClient = new HttpClient();
        }
        
        public async Task<string> UploadFile(string filePath)
        {
            try
            {
                using (var fileStream = System.IO.File.OpenRead(filePath))
                {
                    using (var content = new MultipartFormDataContent())
                    {
                        content.Add(new StreamContent(fileStream), "file", System.IO.Path.GetFileName(filePath));
                        
                        HttpResponseMessage response = await httpClient.PostAsync($"{baseUrl}/upload", content);
                        return await response.Content.ReadAsStringAsync();
                    }
                }
            }
            catch (Exception e)
            {
                Utilities.LogError("Upload file failed", e);
                return null;
            }
        }
        
        public async Task<string> ParseFile(string fileId)
        {
            try
            {
                HttpResponseMessage response = await httpClient.PostAsync($"{baseUrl}/parse?file_id={fileId}", null);
                return await response.Content.ReadAsStringAsync();
            }
            catch (Exception e)
            {
                Utilities.LogError("Parse file failed", e);
                return null;
            }
        }
        
        public async Task<string> ExecuteCommand(string fileId, string command)
        {
            try
            {
                string url = $"{baseUrl}/command?file_id={fileId}&command_text={Uri.EscapeDataString(command)}";
                HttpResponseMessage response = await httpClient.PostAsync(url, null);
                return await response.Content.ReadAsStringAsync();
            }
            catch (Exception e)
            {
                Utilities.LogError("Execute command failed", e);
                return null;
            }
        }
        
        public async Task<string> ValidateFile(string fileId)
        {
            try
            {
                HttpResponseMessage response = await httpClient.PostAsync($"{baseUrl}/validate?file_id={fileId}", null);
                return await response.Content.ReadAsStringAsync();
            }
            catch (Exception e)
            {
                Utilities.LogError("Validate failed", e);
                return null;
            }
        }
    }
}
