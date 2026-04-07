// AutoCADDrawing.cs - Drawing Operations + Live Editing
using Autodesk.AutoCAD.ApplicationServices;
using Autodesk.AutoCAD.DatabaseServices;
using Autodesk.AutoCAD.Geometry;
using System;
using System.Collections.Generic;
using Newtonsoft.Json.Linq;

namespace CADCopilot
{
    public class AutoCADDrawing
    {
        private Document document;
        private Database database;

        public AutoCADDrawing()
        {
            document = Application.DocumentManager.MdiActiveDocument;
            database = document?.Database;
        }

        public void OpenFile(string filePath)
        {
            try
            {
                var doc = Application.DocumentManager.Open(filePath, false);
                document = doc;
                database = doc.Database;
                Utilities.LogInfo($"Opened in AutoCAD: {filePath}");
            }
            catch (Exception e) { Utilities.LogError("OpenFile failed", e); }
        }

        private void RefreshDocument()
        {
            var active = Application.DocumentManager.MdiActiveDocument;
            if (active != null) { document = active; database = active.Database; }
        }

        public void DrawFromApiResponse(string jsonResponse)
        {
            try
            {
                RefreshDocument();
                if (database == null) return;

                var root = JObject.Parse(jsonResponse);
                JToken drawToken = (root["result"] as JObject)?["draw"] ?? root["draw"];
                if (drawToken == null || drawToken.Type != JTokenType.Array) return;

                foreach (var item in (JArray)drawToken)
                {
                    string type  = ((string)item["type"] ?? "").ToLower();
                    string layer = (string)item["layer"] ?? "LPS_BOUNDARY";

                    switch (type)
                    {
                        case "line":
                            DrawLine((double)item["x1"], (double)item["y1"],
                                     (double)item["x2"], (double)item["y2"], layer);
                            break;
                        case "polyline":
                        case "polygon":
                            var pts = new List<(double, double)>();
                            foreach (var pt in (JArray)item["points"])
                                pts.Add(((double)pt[0], (double)pt[1]));
                            DrawPolygon(pts, layer);
                            break;
                        case "circle":
                            DrawCircle((double)item["x"], (double)item["y"],
                                       (double)(item["radius"] ?? 5.0), layer);
                            break;
                        case "text":
                            DrawText((string)item["text"] ?? "",
                                     (double)item["x"], (double)item["y"],
                                     (double)(item["height"] ?? 2.5), layer);
                            break;
                        case "rectangle":
                            double rx = (double)item["x"], ry = (double)item["y"];
                            double rw = (double)item["width"], rh = (double)item["height"];
                            DrawPolygon(new List<(double, double)>
                            {
                                (rx, ry), (rx+rw, ry), (rx+rw, ry+rh), (rx, ry+rh)
                            }, layer);
                            break;
                    }
                }
                ZoomExtents();
            }
            catch (Exception e) { Utilities.LogError("DrawFromApiResponse failed", e); }
        }

        public void ZoomExtents()
        {
            try { document?.SendStringToExecute("ZOOM\nE\n", true, false, false); }
            catch { }
        }

        public void DrawPolygon(List<(double x, double y)> points, string layerName = "LPS_BOUNDARY")
        {
            try
            {
                RefreshDocument();
                using var t = database.TransactionManager.StartTransaction();
                CreateLayerIfNotExists(layerName, t);
                var poly = new Polyline();
                poly.SetDatabaseDefaults();
                for (int i = 0; i < points.Count; i++)
                    poly.AddVertexAt(i, new Point2d(points[i].x, points[i].y), 0, 0, 0);
                poly.Closed = true;
                poly.Layer  = layerName;
                AddToModelSpace(poly, t);
                t.Commit();
            }
            catch (Exception e) { Utilities.LogError("DrawPolygon failed", e); }
        }

        public void DrawLine(double x1, double y1, double x2, double y2, string layerName = "LPS_CORRIDOR")
        {
            try
            {
                RefreshDocument();
                using var t = database.TransactionManager.StartTransaction();
                CreateLayerIfNotExists(layerName, t);
                var line = new Line(new Point3d(x1, y1, 0), new Point3d(x2, y2, 0)) { Layer = layerName };
                AddToModelSpace(line, t);
                t.Commit();
            }
            catch (Exception e) { Utilities.LogError("DrawLine failed", e); }
        }

        public void DrawText(string text, double x, double y, double height = 2.5, string layerName = "LPS_TEXT")
        {
            try
            {
                RefreshDocument();
                using var t = database.TransactionManager.StartTransaction();
                CreateLayerIfNotExists(layerName, t);
                var dbText = new DBText();
                dbText.SetDatabaseDefaults();
                dbText.Position   = new Point3d(x, y, 0);
                dbText.TextString = text;
                dbText.Height     = height;
                dbText.Layer      = layerName;
                AddToModelSpace(dbText, t);
                t.Commit();
            }
            catch (Exception e) { Utilities.LogError("DrawText failed", e); }
        }

        public void DrawCircle(double x, double y, double radius, string layerName = "LPS_TOWER")
        {
            try
            {
                RefreshDocument();
                using var t = database.TransactionManager.StartTransaction();
                CreateLayerIfNotExists(layerName, t);
                var circle = new Circle(new Point3d(x, y, 0), Vector3d.ZAxis, radius) { Layer = layerName };
                AddToModelSpace(circle, t);
                t.Commit();
            }
            catch (Exception e) { Utilities.LogError("DrawCircle failed", e); }
        }

        public void ClearLayer(string layerName)
        {
            try
            {
                RefreshDocument();
                using var t = database.TransactionManager.StartTransaction();
                var bt = (BlockTable)t.GetObject(database.BlockTableId, OpenMode.ForRead);
                var ms = (BlockTableRecord)t.GetObject(bt[BlockTableRecord.ModelSpace], OpenMode.ForWrite);
                foreach (ObjectId id in ms)
                {
                    var entity = (Entity)t.GetObject(id, OpenMode.ForRead);
                    if (entity.Layer == layerName) { entity.UpgradeOpen(); entity.Erase(); }
                }
                t.Commit();
            }
            catch (Exception e) { Utilities.LogError("ClearLayer failed", e); }
        }

        private void AddToModelSpace(Entity entity, Transaction t)
        {
            var bt = (BlockTable)t.GetObject(database.BlockTableId, OpenMode.ForRead);
            var ms = (BlockTableRecord)t.GetObject(bt[BlockTableRecord.ModelSpace], OpenMode.ForWrite);
            ms.AppendEntity(entity);
            t.AddNewlyCreatedDBObject(entity, true);
        }

        private void CreateLayerIfNotExists(string layerName, Transaction t)
        {
            try
            {
                var lt = (LayerTable)t.GetObject(database.LayerTableId, OpenMode.ForRead);
                if (!lt.Has(layerName))
                {
                    lt.UpgradeOpen();
                    var newLayer = new LayerTableRecord { Name = layerName };
                    lt.Add(newLayer);
                    t.AddNewlyCreatedDBObject(newLayer, true);
                }
            }
            catch (Exception e) { Utilities.LogError("CreateLayer failed", e); }
        }
    }
}