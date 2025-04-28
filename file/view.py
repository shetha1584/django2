from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import TranslationForm, TextInputForm, YouTubeURLForm
from googletrans import Translator
from youtube_transcript_api import YouTubeTranscriptApi
import PyPDF2

def home(request):
    translated_text = None

    if request.method == 'POST':
        form = TranslationForm(request.POST, request.FILES)
        if form.is_valid():
            translation = form.save(commit=False)

            translator = Translator()

            if translation.content_type == 'text':
                input_text_form = TextInputForm(request.POST)
                if input_text_form.is_valid():
                    input_text = input_text_form.cleaned_data['input_text']
                    translated_text = translator.translate(
                        input_text,
                        src=translation.source_language,
                        dest=translation.destination_language
                    ).text

            elif translation.content_type == 'pdf':
                pdf_file = request.FILES.get('pdf_input')
                if pdf_file:
                    reader = PyPDF2.PdfReader(pdf_file)
                    text = ''
                    for page in reader.pages:
                        text += page.extract_text()
                    translated_text = translator.translate(
                        text,
                        src=translation.source_language,
                        dest=translation.destination_language
                    ).text

            elif translation.content_type == 'youtube':
                youtube_form = YouTubeURLForm(request.POST)
                if youtube_form.is_valid():
                    youtube_url = youtube_form.cleaned_data['youtube_url']
                    video_id = extract_video_id(youtube_url)
                    transcript = YouTubeTranscriptApi.get_transcript(video_id)
                    full_text = ' '.join([entry['text'] for entry in transcript])
                    translated_text = translator.translate(
                        full_text,
                        src=translation.source_language,
                        dest=translation.destination_language
                    ).text

            if translated_text:
                request.session['translated_text'] = translated_text
                return redirect('translation_success')

    else:
        form = TranslationForm()

    context = {'form': form}
    return render(request, 'home.html', context)

def translation_success(request):
    translated_text = request.session.get('translated_text', '')
    return render(request, 'translation_success.html', {'translated_text': translated_text})

def download_translation(request):
    translated_text = request.session.get('translated_text', '')
    response = HttpResponse(translated_text, content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename="translated_text.txt"'
    return response

def extract_video_id(url):
    """
    Extract the video ID from a YouTube URL.
    """
    if "v=" in url:
        return url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[1]
    return url
