// AutoCADDrawing.cs - Drawing Operations
using Autodesk.AutoCAD.ApplicationServices;
using Autodesk.AutoCAD.DatabaseServices;
using Autodesk.AutoCAD.Geometry;
using System;
using System.Collections.Generic;

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
        
        public void DrawPolygon(List<(double x, double y)> points, string layerName = "0")
        {
            try
            {
                using (Transaction transaction = database.TransactionManager.StartTransaction())
                {
                    // Create layer if not exists
                    CreateLayerIfNotExists(layerName, transaction);
                    
                    // Create polyline
                    Polyline polyline = new Polyline();
                    polyline.SetDatabaseDefaults();
                    
                    for (int i = 0; i < points.Count; i++)
                    {
                        polyline.AddVertexAt(i, new Point2d(points[i].x, points[i].y), 0, 0, 0);
                    }
                    
                    polyline.Closed = true;
                    polyline.Layer = layerName;
                    polyline.Color = Autodesk.AutoCAD.Colors.Color.FromColorIndex(Autodesk.AutoCAD.Colors.ColorMethod.ByAci, 1);
                    
                    // Add to model space
                    BlockTable blockTable = (BlockTable)transaction.GetObject(database.BlockTableId, OpenMode.ForRead);
                    BlockTableRecord modelSpace = (BlockTableRecord)transaction.GetObject(blockTable[BlockTableRecord.ModelSpace], OpenMode.ForWrite);
                    modelSpace.AppendEntity(polyline);
                    transaction.AddNewlyCreatedDBObject(polyline, true);
                    
                    transaction.Commit();
                }
            }
            catch (Exception e)
            {
                Utilities.LogError("Draw polygon failed", e);
            }
        }
        
        public void DrawLine(double x1, double y1, double x2, double y2, string layerName = "0")
        {
            try
            {
                using (Transaction transaction = database.TransactionManager.StartTransaction())
                {
                    CreateLayerIfNotExists(layerName, transaction);
                    
                    Line line = new Line(new Point3d(x1, y1, 0), new Point3d(x2, y2, 0));
                    line.Layer = layerName;
                    
                    BlockTable blockTable = (BlockTable)transaction.GetObject(database.BlockTableId, OpenMode.ForRead);
                    BlockTableRecord modelSpace = (BlockTableRecord)transaction.GetObject(blockTable[BlockTableRecord.ModelSpace], OpenMode.ForWrite);
                    modelSpace.AppendEntity(line);
                    transaction.AddNewlyCreatedDBObject(line, true);
                    
                    transaction.Commit();
                }
            }
            catch (Exception e)
            {
                Utilities.LogError("Draw line failed", e);
            }
        }
        
        public void ClearLayer(string layerName)
        {
            try
            {
                using (Transaction transaction = database.TransactionManager.StartTransaction())
                {
                    BlockTable blockTable = (BlockTable)transaction.GetObject(database.BlockTableId, OpenMode.ForRead);
                    BlockTableRecord modelSpace = (BlockTableRecord)transaction.GetObject(blockTable[BlockTableRecord.ModelSpace], OpenMode.ForWrite);
                    
                    foreach (ObjectId id in modelSpace)
                    {
                        Entity entity = (Entity)transaction.GetObject(id, OpenMode.ForRead);
                        if (entity.Layer == layerName)
                        {
                            entity.UpgradeOpen();
                            entity.Erase();
                        }
                    }
                    
                    transaction.Commit();
                }
            }
            catch (Exception e)
            {
                Utilities.LogError("Clear layer failed", e);
            }
        }
        
        private void CreateLayerIfNotExists(string layerName, Transaction transaction)
        {
            try
            {
                LayerTable layerTable = (LayerTable)transaction.GetObject(database.LayerTableId, OpenMode.ForRead);
                
                if (!layerTable.Has(layerName))
                {
                    layerTable.UpgradeOpen();
                    LayerTableRecord newLayer = new LayerTableRecord();
                    newLayer.Name = layerName;
                    layerTable.Add(newLayer);
                    transaction.AddNewlyCreatedDBObject(newLayer, true);
                }
            }
            catch (Exception e)
            {
                Utilities.LogError("Create layer failed", e);
            }
        }
    }
}
