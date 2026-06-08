import type { Cut } from '../types/generation';
import { StatusBadge } from './StatusBadge';

export function CutCard({ cut }: { cut: Cut }) {
  const completedVideo = cut.images
    .flatMap((img) => img.videos)
    .find((v) => v.status === 'completed' && v.video_url);

  const completedImage = cut.images.find(
    (img) => img.status === 'completed' && img.image_url,
  );

  return (
    <div className="cut-card">
      <div className="cut-header">
        <span className="cut-label">Cut {cut.order + 1}</span>
        <StatusBadge status={cut.status} />
      </div>

      {completedVideo ? (
        <video
          src={completedVideo.video_url!}
          controls
          className="cut-media"
          poster={completedImage?.image_url ?? undefined}
        />
      ) : completedImage ? (
        <img src={completedImage.image_url!} alt={`Cut ${cut.order + 1}`} className="cut-media" />
      ) : (
        <div className="cut-placeholder">
          {cut.status === 'processing' ? (
            <div className="spinner" />
          ) : cut.status === 'failed' ? (
            <span>Generation failed</span>
          ) : (
            <span>Waiting...</span>
          )}
        </div>
      )}

      <div className="cut-prompts">
        <p><strong>Image:</strong> {cut.image_prompt}</p>
        <p><strong>Motion:</strong> {cut.video_prompt}</p>
      </div>
    </div>
  );
}
