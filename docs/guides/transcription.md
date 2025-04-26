# Transcription & AI Summaries

ThinkiPlex includes powerful features for transcribing course audio and generating AI summaries, allowing you to enhance your learning experience and create a searchable knowledge base from your courses.

## Overview

The transcription and AI summary features work together to:

1. Extract audio from course videos
2. Transcribe the audio using AssemblyAI with speaker diarization
3. Generate AI summaries from the transcriptions using Claude AI
4. Organize the results in a structured format

## Prerequisites

Before using the transcription features, ensure you have:

1. An [AssemblyAI API key](https://www.assemblyai.com/) for transcription services
2. An [Anthropic API key](https://www.anthropic.com/) for Claude AI summaries
3. Properly configured your `config/thinkiplex.yaml` file (see [Configuration](configuration.md))

## Configuration

### AssemblyAI Configuration

Add your AssemblyAI API key to your environment variables:

```bash
export ASSEMBLYAI_API_KEY="your-api-key-here"
```

For persistent configuration, add it to your shell profile file (`.bashrc`, `.zshrc`, etc.).

### Claude AI Configuration

Add your Anthropic API key to your environment variables:

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

Configure Claude AI models and prompts in your `config/thinkiplex.yaml` file:

```yaml
claude:
  models:
    claude-3-7-sonnet-latest:
      name: "Claude 3.7 Sonnet"
      context_window: 200000
      max_output_tokens: 8192
      description: "Latest Claude model with hybrid reasoning capabilities"
      is_default: true
    claude-3-5-sonnet-latest:
      name: "Claude 3.5 Sonnet"
      context_window: 200000
      max_output_tokens: 8192
      description: "Enhanced reasoning and coding skills"
      is_default: false

  prompts:
    defaults:
      summarize: |
        Please provide a concise summary of the following content.
      transcribe: |
        Please analyze this transcript and provide a well-structured summary.
      analyze: |
        Please perform a detailed analysis of the following content.
      comprehensive: |
        ===Comprehensive Content Summarizer===

        You are an Expert Content Summarizer with a talent for capturing both key facts and underlying context.
      course_notes: |
        ===Course Notes Generator===

        Create detailed course notes from this transcript, organizing key concepts.
```

See the [Configuration Guide](configuration.md) for more details.

## Usage

### Basic Usage

To transcribe and generate summaries for a course:

```bash
python -m thinkiplex process course-name --transcribe
```

This will:

1. Process the course materials
2. Extract audio if needed
3. Transcribe the audio files
4. Generate AI summaries based on the transcriptions

### Advanced Options

#### Specify Claude Model

Choose which Claude model to use for summaries:

```bash
python -m thinkiplex process course-name --transcribe --claude-model claude-3-7-sonnet-latest
```

#### Disable Speaker Diarization

If you don't need speaker identification in transcripts:

```bash
python -m thinkiplex process course-name --transcribe --no-diarization
```

#### Choose Prompt Type

Select different prompt types for different summary styles:

```bash
python -m thinkiplex process course-name --transcribe --prompt-type course_notes
```

Available prompt types:

- `summarize`: Basic summary focusing on key points
- `transcribe`: Summary specifically designed for transcripts
- `analyze`: Detailed analysis with themes, arguments, and insights
- `comprehensive`: In-depth summary capturing key facts, context, and nuances
- `course_notes`: Structured course notes with key concepts and actionable takeaways

#### Reprocess Existing Summaries

To regenerate summaries for files that already have summaries:

```bash
python -m thinkiplex process course-name --transcribe --reprocess-summaries
```

This option is useful when:

- You want to try a different Claude model
- You want to use a different prompt type
- You want to regenerate summaries with improved AI models
- You've made changes to the prompt templates

#### Process Specific Sessions

Process only specific sessions of a course:

```bash
python -m thinkiplex process course-name --transcribe --sessions 1,2,3
```

## Output Structure

The transcription and summary outputs are organized as follows:

```
data/courses/course-name/
├── downloads/
│   └── session-1/
│       ├── audio/
│       │   └── session-1.mp3
│       ├── transcripts/
│       │   └── session-1_transcript.txt
│       └── summaries/
│           └── session-1_summary.md
```

- **Transcripts**: Plain text files with speaker-diarized transcriptions
- **Summaries**: Markdown files with AI-generated summaries

## Troubleshooting

### Missing Transcriptions

If transcriptions are not being generated:

1. Check that your AssemblyAI API key is correctly set
2. Verify that audio files exist in the expected location
3. Check the logs for any API errors

### Summary Generation Issues

If summaries are not being generated:

1. Ensure your Anthropic API key is correctly set
2. Verify that transcription files exist
3. Check that the Claude model specified is available
4. Review the logs for any API errors or rate limiting

## Best Practices

1. **Start Small**: Test with a single session before processing an entire course
2. **Choose the Right Prompt**: Different prompt types work better for different content
3. **Use Speaker Diarization**: For interview or multi-speaker content, speaker diarization improves summary quality
4. **Review and Refine**: Periodically review the generated summaries and adjust prompts as needed
