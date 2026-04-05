// APIClient.cs - API Communication
using System;
using System.Net.Http;
using System.Threading.Tasks;
using System.IO;
using Newtonsoft.Json.Linq;

namespace CADCopilot
{
    public class APIClient
    {
        private readonly string baseUrl;
        private readonly HttpClient httpClient;

        public APIClient(string url)
        {
            baseUrl    = url.TrimEnd('/');
            httpClient = new HttpClient { Timeout = TimeSpan.FromSeconds(120) };
        }

        // Upload DWG or DXF file → returns file_id
        public async Task<string> UploadDwg(string filePath)
        {
            try
            {
                using var stream  = File.OpenRead(filePath);
                using var content = new MultipartFormDataContent();
                content.Add(new StreamContent(stream), "file", Path.GetFileName(filePath));

                var response = await httpClient.PostAsync($"{baseUrl}/upload", content);
                var json     = await response.Content.ReadAsStringAsync();
                var doc      = JObject.Parse(json);
                return (string)doc["file_id"];
            }
            catch (System.Exception e)
            {
                Utilities.LogError("UploadDwg failed", e);
                return null;
            }
        }

        // Upload Excel file → returns excel_id
        public async Task<string> UploadExcel(string filePath)
        {
            try
            {
                using var stream  = File.OpenRead(filePath);
                using var content = new MultipartFormDataContent();
                content.Add(new StreamContent(stream), "file", Path.GetFileName(filePath));

                var response = await httpClient.PostAsync($"{baseUrl}/upload-excel", content);
                var json     = await response.Content.ReadAsStringAsync();
                var doc      = JObject.Parse(json);
                return (string)doc["excel_id"];
            }
            catch (System.Exception e)
            {
                Utilities.LogError("UploadExcel failed", e);
                return null;
            }
        }

        // Auto draw LPS → returns output_id + parcels count
        public async Task<(string outputId, int parcelsDrawn)> AutoDraw(string fileId, string excelId)
        {
            try
            {
                var url      = $"{baseUrl}/auto-draw?file_id={fileId}&excel_id={excelId}";
                var response = await httpClient.PostAsync(url, null);
                var json     = await response.Content.ReadAsStringAsync();
                var doc      = JObject.Parse(json);
                var outputId = (string)doc["output_id"];
                var parcels  = (int)doc["parcels_drawn"];
                return (outputId, parcels);
            }
            catch (System.Exception e)
            {
                Utilities.LogError("AutoDraw failed", e);
                return (null, 0);
            }
        }

        // Execute chat command → returns AI response
        public async Task<string> ExecuteCommand(string fileId, string command)
        {
            try
            {
                var url      = $"{baseUrl}/command?file_id={fileId}&command_text={Uri.EscapeDataString(command)}";
                var response = await httpClient.PostAsync(url, null);
                var json     = await response.Content.ReadAsStringAsync();
                var doc      = JObject.Parse(json);

                if (doc.ContainsKey("result"))
                    return (string)doc["result"];

                return json;
            }
            catch (System.Exception e)
            {
                Utilities.LogError("ExecuteCommand failed", e);
                return $"Error: {e.Message}";
            }
        }

        // Download output DXF/DWG file
        public async Task<string> DownloadOutput(string outputId, string savePath)
        {
            try
            {
                var response = await httpClient.GetAsync($"{baseUrl}/download/{outputId}");
                var bytes    = await response.Content.ReadAsByteArrayAsync();
                File.WriteAllBytes(savePath, bytes);
                return savePath;
            }
            catch (System.Exception e)
            {
                Utilities.LogError("DownloadOutput failed", e);
                return null;
            }
        }
    }
}