import YOLOv11Upload from "./YOLOv11Upload";

/*
 Dashboard comp - Simple YOLOv11 Upload Interface
 - Upload file (image/video)
 - Select model type (enhancement, tracking, counter)
 - Display output
*/
export default function Dashboard() {
  return (
    <div className="space-y-6">
      <YOLOv11Upload />
    </div>
  );
}
