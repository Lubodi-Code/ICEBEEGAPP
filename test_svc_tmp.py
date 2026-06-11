import sys
sys.path.insert(0,'packages/dto/src')
from iceberg_negocio.factory import get_video_service
from iceberg_dto import VideoRequest

req = VideoRequest(
    iceberg_title="Misterios del Oceano",
    level_number=1, level_name="Superficie",
    entry_title="El comienzo",
    description=("Bienvenido al iceberg de los misterios. En este primer nivel exploramos "
                 "lo que todos conocen, pero pronto descenderemos hacia las profundidades "
                 "donde se esconden los secretos mas oscuros narrados por la voz de Loquendo."),
)
svc = get_video_service()
mp4 = svc.generate(req)
print("MP4_OUT=" + mp4)
