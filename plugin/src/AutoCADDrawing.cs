// AutoCADDrawing.cs - Drawing Operations
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
            database = document.Database;
        }

        // Draw polygon/boundary
        public void DrawPolygon(List<(double x, double y)> points, string layerName = "LPS_BOUNDARY")
        {
            try
            {
                using var transaction = database.TransactionManager.StartTransaction();
                CreateLayerIfNotExists(layerName, transaction);

                var polyline = new Polyline();
                polyline.SetDatabaseDefaults();

                for (int i = 0; i < points.Count; i++)
                    polyline.AddVertexAt(i, new Point2d(points[i].x, points[i].y), 0, 0, 0);

                polyline.Closed = true;
                polyline.Layer = layerName;

                AddToModelSpace(polyline, transaction);
                transaction.Commit();
            }
            catch (Exception e) { Utilities.LogError("DrawPolygon failed", e); }
        }

        // Draw line
        public void DrawLine(double x1, double y1, double x2, double y2, string layerName = "LPS_CORRIDOR")
        {
            try
            {
                using var transaction = database.TransactionManager.StartTransaction();
                CreateLayerIfNotExists(layerName, transaction);

                var line = new Line(new Point3d(x1, y1, 0), new Point3d(x2, y2, 0));
                line.Layer = layerName;

                AddToModelSpace(line, transaction);
                transaction.Commit();
            }
            catch (Exception e) { Utilities.LogError("DrawLine failed", e); }
        }

        // Draw text label
        public void DrawText(string text, double x, double y, double height = 2.5, string layerName = "LPS_TEXT")
        {
            try
            {
                using var transaction = database.TransactionManager.StartTransaction();
                CreateLayerIfNotExists(layerName, transaction);

                var dbText = new DBText();
                dbText.SetDatabaseDefaults();
                dbText.Position = new Point3d(x, y, 0);
                dbText.TextString = text;
                dbText.Height = height;
                dbText.Layer = layerName;

                AddToModelSpace(dbText, transaction);
                transaction.Commit();
            }
            catch (Exception e) { Utilities.LogError("DrawText failed", e); }
        }

        // Draw circle (tower marker)
        public void DrawCircle(double x, double y, double radius, string layerName = "LPS_TOWER")
        {
            try
            {
                using var transaction = database.TransactionManager.StartTransaction();
                CreateLayerIfNotExists(layerName, transaction);

                var circle = new Circle(new Point3d(x, y, 0), Vector3d.ZAxis, radius);
                circle.Layer = layerName;

                AddToModelSpace(circle, transaction);
                transaction.Commit();
            }
            catch (Exception e) { Utilities.LogError("DrawCircle failed", e); }
        }

        // Draw from API JSON response
        public void DrawFromApiResponse(string jsonResponse)
        {
            try
            {
                var doc = JObject.Parse(jsonResponse);
                var result = doc["result"] as JObject;
                if (result == null) return;

                string type = (string)result["type"] ?? "";

                if (type == "polygon" && result["points"] != null)
                {
                    var points = new List<(double x, double y)>();
                    foreach (var pt in (JArray)result["points"])
                        points.Add(((double)pt[0], (double)pt[1]));
                    DrawPolygon(points);
                }
                else if (type == "dimension" && result["point1"] != null)
                {
                    var p1 = (JArray)result["point1"];
                    var p2 = (JArray)result["point2"];
                    DrawLine((double)p1[0], (double)p1[1], (double)p2[0], (double)p2[1]);
                }
            }
            catch (Exception e) { Utilities.LogError("DrawFromApiResponse failed", e); }
        }

        // Clear all entities on a layer
        public void ClearLayer(string layerName)
        {
            try
            {
                using var transaction = database.TransactionManager.StartTransaction();
                var blockTable = (BlockTable)transaction.GetObject(database.BlockTableId, OpenMode.ForRead);
                var modelSpace = (BlockTableRecord)transaction.GetObject(blockTable[BlockTableRecord.ModelSpace], OpenMode.ForWrite);

                foreach (ObjectId id in modelSpace)
                {
                    var entity = (Entity)transaction.GetObject(id, OpenMode.ForRead);
                    if (entity.Layer == layerName)
                    {
                        entity.UpgradeOpen();
                        entity.Erase();
                    }
                }
                transaction.Commit();
            }
            catch (Exception e) { Utilities.LogError("ClearLayer failed", e); }
        }

        private void AddToModelSpace(Entity entity, Transaction transaction)
        {
            var blockTable = (BlockTable)transaction.GetObject(database.BlockTableId, OpenMode.ForRead);
            var modelSpace = (BlockTableRecord)transaction.GetObject(blockTable[BlockTableRecord.ModelSpace], OpenMode.ForWrite);
            modelSpace.AppendEntity(entity);
            transaction.AddNewlyCreatedDBObject(entity, true);
        }

        private void CreateLayerIfNotExists(string layerName, Transaction transaction)
        {
            try
            {
                var layerTable = (LayerTable)transaction.GetObject(database.LayerTableId, OpenMode.ForRead);
                if (!layerTable.Has(layerName))
                {
                    layerTable.UpgradeOpen();
                    var newLayer = new LayerTableRecord { Name = layerName };
                    layerTable.Add(newLayer);
                    transaction.AddNewlyCreatedDBObject(newLayer, true);
                }
            }
            catch (Exception e) { Utilities.LogError("CreateLayer failed", e); }
        }
    }
}