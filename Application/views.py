import ffmpeg
import time
import json
import os


from django.http import JsonResponse, FileResponse, HttpResponseRedirect, Http404
from django.views.decorators.csrf import csrf_exempt
from lib2to3.fixes.fix_input import context
from django.http import HttpResponse
from django.shortcuts import render
from django.conf import settings
from yt_dlp import YoutubeDL


def home(request):
    return render(request, "base.html")

def downloader(request):
    d = request.GET.get('d')
    data = {}
    if d == "0":
        data["data"] = "Ютуба"
    elif d == "1":
        data["data"] = "Тиктока"
    else:
        print(d, type(d))

    return render(request, "downloader.html", context=data)

def process_video(request):
    if request.method == 'POST':
        try:
            # Извлечение ссылки
            data = json.loads(request.body)
            video_url = data.get('youtube_link', '')

            if not video_url:
                return JsonResponse({"status": "error", "message": "Ссылка не передана", "thumbnail": "/media/cat.jpg"})

            # Настройки yt_dlp
            ydl_opts = {
                'format': 'best',
                'quiet': True,
                'proxy': '',
                # curl -x  https://www.youtube.com
                'cookiefile': 'media/cookies.txt',
                # 'cookiesfrombrowser': ('firefox',),
            }

            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)

                # Получение данных о видео
                video_title = info.get('title', 'Без названия')
                thumbnail = info.get('thumbnail', '/media/cat.jpg')
                formats = info.get('formats', [])

                fgh = ""
                for f in formats:
                    fgh += str(f) + "\n"

                flp = open("lol.txt", "w")
                flp.write(fgh)
                flp.close()

                # Ограниченные форматы для кнопок
                allowed_formats = ['144p', '360p', '480p', '720p', '1080p', '1440p', '2160p']  # 2160p = 4k
                audio_formats = [f for f in formats if f.get('vcodec') == 'none']  # Только аудио

                # Удалить дубликаты по разрешению
                unique_formats = {}
                for fmt in formats:
                    format_note = fmt.get('format_note')
                    if format_note in allowed_formats:
                        if format_note not in unique_formats:
                            unique_formats[format_note] = fmt
                        else:
                            # Сохраняем формат с наилучшим битрейтом
                            if fmt.get('tbr', 0) > unique_formats[format_note].get('tbr', 0):
                                unique_formats[format_note] = fmt

                video_formats = list(unique_formats.values())

                # Создание кнопок для скачивания
                buttons = []

                # Добавить кнопку для аудио
                if audio_formats:
                    best_audio = max(audio_formats, key=lambda x: x.get('abr') or 0)  # Лучшая аудио-дорожка
                    buttons.append({
                        "text": "Скачать аудио",
                        "action": best_audio['format_id'] + ";1"
                    })

                # Добавить кнопки для видео
                for fmt in video_formats:
                    buttons.append({
                        "text": f"Скачать {fmt['format_note']}",
                        "action": str(fmt['format_id']) + "+" + str(best_audio['format_id']) + ";0"
                    })

            return JsonResponse({
                "status": "success",
                "video_title": video_title,
                "thumbnail": thumbnail,
                "buttons": buttons
            })

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e), "thumbnail": "/media/cat.png"})
    return JsonResponse({"status": "error", "message": "Только POST запросы разрешены"})


def delete_all_files_in_folder(folder_path):
    try:
        # Получаем список всех файлов и папок в директории
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)

            # Проверяем, является ли объект файлом
            if os.path.isfile(file_path):
                os.remove(file_path)  # Удаляем файл
                # print(f"Удалён файл: {file_path}")
            elif os.path.isdir(file_path):
                pass
                # print(f"Пропущена папка: {file_path}")
    except Exception as e:
        pass
        # print(f"Произошла ошибка: {e}")

@csrf_exempt
def download_video(request):
    if request.method == 'POST':
        try:
            # Получение ссылки из запроса
            data = json.loads(request.body)
            video_url = data.get('youtube_link', '')
            format = data.get('format', 'bestvideo+bestaudio').split(';')
            format_id = format[0]
            file_extension = int(format[1])

            # Шаг 1: Создаём уникальные имена файлов на основе текущего времени
            timestamp = str(int(time.time()))
            base_dir = 'downloads'  # Директория для временных файлов
            os.makedirs(base_dir, exist_ok=True)

            temp_video_path = os.path.join(base_dir, f"{timestamp}_video.mp4")
            temp_audio_path = os.path.join(base_dir, f"{timestamp}_input.mp3")
            output_audio_path = os.path.join(base_dir, f"{timestamp}_output.mp3")
            output_video_path = os.path.join(base_dir, f"{timestamp}_output.mp4")

            if file_extension == 1:
                print("AUDIO-AUDIO-AUDIO-AUDIO-AUDIO-AUDIO-AUDIO-AUDIO-AUDIO-AUDIO-AUDIO")
                ydl_opts = {
                    'format': format_id,  # аудио
                    'outtmpl': temp_audio_path,  # Путь для сохранения файла
                }

                with YoutubeDL(ydl_opts) as ydl:
                    ydl.download([video_url])

                ffmpeg.input(temp_audio_path).output(
                    output_audio_path,
                    format='mp3',  # Указываем выходной формат
                    acodec='libmp3lame'  # Кодек MP3
                ).overwrite_output().run()

                response = FileResponse(
                    open(output_audio_path, 'rb'),
                    as_attachment=True,
                    filename=f'processed_audio_{timestamp}.mp3'
                )
            else:
                print("VIDEO-VIDEO-VIDEO-VIDEO-VIDEO-VIDEO-VIDEO-VIDEO-VIDEO-VIDEO-VIDEO")
                # Скачивание видео с YouTube
                ydl_opts = {
                    'format': format_id,  # Лучшее видео и аудио
                    'outtmpl': temp_video_path,  # Путь для сохранения файла
                    'merge_output_format': 'mp4',  # Объединение в MP4
                }

                with YoutubeDL(ydl_opts) as ydl:
                    ydl.download([video_url])

                # Перекодировка видео с помощью ffmpeg
                ffmpeg.input(temp_video_path).output(
                    output_video_path,
                    vcodec='libx264',  # Новый видеокодек
                    acodec='aac',  # Новый аудиокодек
                ).overwrite_output().run()

                # Отправка файла пользователю через FileResponse
                response = FileResponse(
                    open(output_video_path, 'rb'),
                    as_attachment=True,
                    filename=f'processed_video_{timestamp}.mp4'
                )

            return response

        except Exception as e:
            raise Http404(f"Ошибка обработки видео: {e}")

        finally:
            delete_all_files_in_folder(base_dir)
    return JsonResponse({"status": "error", "message": "Только POST запросы разрешены"})
