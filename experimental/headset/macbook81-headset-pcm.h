/* SPDX-License-Identifier: GPL-2.0-or-later */
/* Experimental headset capture for MacBook8,1, CS4208 SSID 106b:6400.
 *
 * Research: pmgart/macbook8-1-debian-guide, commit
 * 86e996c987f01144e671569e56277f9223a1519b, and the existing
 * thomas-shirley/macbook8.1-speaker-driver speaker implementation.
 * New experiment: isolate the headset on ADC 0x07; bias only during capture.
 * Does not claim working audio or simultaneous TDM speaker operation.
 */
static unsigned int mb81_headset_bias = 1;
module_param(mb81_headset_bias, uint, 0644);
MODULE_PARM_DESC(mb81_headset_bias, "Experimental headset VREF: 0=HiZ, 1=50%, 4=80%; change only while capture is closed");

static unsigned int mb81_headset_clock(struct hda_codec *codec)
{
	unsigned int index, clock;

	index = snd_hda_codec_read(codec, 0x24, 0, AC_VERB_GET_COEF_INDEX, 0);
	snd_hda_codec_write(codec, 0x24, 0, AC_VERB_SET_COEF_INDEX, 0x1f);
	clock = snd_hda_codec_read(codec, 0x24, 0, AC_VERB_GET_PROC_COEF, 0);
	snd_hda_codec_write(codec, 0x24, 0, AC_VERB_SET_COEF_INDEX, index);
	return clock;
}

static void mb81_headset_snapshot(struct hda_codec *codec, const char *stage)
{
    codec_info(codec,
        "MB81 HEADSET %s: ADC7 power=0x%x stream=0x%x format=0x%x select=0x%x pin18 power=0x%x control=0x%x sense=0x%x clock=0x%x\n",
        stage,
        snd_hda_codec_read(codec, 0x07, 0, AC_VERB_GET_POWER_STATE, 0),
        snd_hda_codec_read(codec, 0x07, 0, AC_VERB_GET_CONV, 0),
        snd_hda_codec_read(codec, 0x07, 0, AC_VERB_GET_STREAM_FORMAT, 0),
        snd_hda_codec_read(codec, 0x07, 0, AC_VERB_GET_CONNECT_SEL, 0),
        snd_hda_codec_read(codec, 0x18, 0, AC_VERB_GET_POWER_STATE, 0),
        snd_hda_codec_read(codec, 0x18, 0, AC_VERB_GET_PIN_WIDGET_CONTROL, 0),
        snd_hda_codec_read(codec, 0x18, 0, AC_VERB_GET_PIN_SENSE, 0),
        mb81_headset_clock(codec));
}

static void mb81_headset_restore(struct hda_codec *codec)
{
	struct cs_spec *spec = codec->spec;

	if (!spec->headset_active)
		return;
	mb81_headset_snapshot(codec, "before cleanup");
	snd_hda_codec_cleanup_stream(codec, 0x07);
	snd_hda_codec_write(codec, 0x18, 0, AC_VERB_SET_PIN_WIDGET_CONTROL,
			    spec->headset_pin_ctl);
	snd_hda_codec_write(codec, 0x07, 0, AC_VERB_SET_CONNECT_SEL,
			    spec->headset_adc_sel);
	snd_hda_codec_write(codec, 0x07, 0, AC_VERB_SET_AMP_GAIN_MUTE,
		AC_AMP_SET_INPUT | AC_AMP_SET_LEFT | (1 << AC_AMP_SET_INDEX_SHIFT) |
		spec->headset_amp_left);
	snd_hda_codec_write(codec, 0x07, 0, AC_VERB_SET_AMP_GAIN_MUTE,
		AC_AMP_SET_INPUT | AC_AMP_SET_RIGHT | (1 << AC_AMP_SET_INDEX_SHIFT) |
		spec->headset_amp_right);
	snd_hda_codec_write(codec, 0x18, 0, AC_VERB_SET_POWER_STATE,
			    spec->headset_pin_power);
	snd_hda_codec_write(codec, 0x07, 0, AC_VERB_SET_POWER_STATE,
			    spec->headset_adc_power);
	spec->headset_active = false;
	codec_info(codec, "MacBook8,1 headset released: clock=0x%x\n",
		   mb81_headset_clock(codec));
}

static int mb81_headset_prepare(struct hda_pcm_stream *hinfo,
		struct hda_codec *codec, unsigned int stream_tag,
		unsigned int format, struct snd_pcm_substream *substream)
{
	struct cs_spec *spec = codec->spec;

	mb81_headset_restore(codec);
    codec_info(codec, "MB81 HEADSET prepare requested tag=%u format=0x%x bias=%u\n",
               stream_tag, format, mb81_headset_bias);
    mb81_headset_snapshot(codec, "before prepare");
	if (mb81_headset_bias != 0 && mb81_headset_bias != 1 && mb81_headset_bias != 4)
		return -EINVAL;
	if (!(snd_hda_codec_read(codec, 0x10, 0, AC_VERB_GET_PIN_SENSE, 0) &
	      AC_PINSENSE_PRESENCE))
		return -ENODEV;
	if (mb81_headset_clock(codec) != 0)
		return -EIO;
	spec->headset_pin_ctl = snd_hda_codec_read(codec, 0x18, 0,
						AC_VERB_GET_PIN_WIDGET_CONTROL, 0);
	spec->headset_pin_power = snd_hda_codec_read(codec, 0x18, 0,
						AC_VERB_GET_POWER_STATE, 0) & 0xf;
	spec->headset_adc_power = snd_hda_codec_read(codec, 0x07, 0,
						AC_VERB_GET_POWER_STATE, 0) & 0xf;
	spec->headset_adc_sel = snd_hda_codec_read(codec, 0x07, 0,
						AC_VERB_GET_CONNECT_SEL, 0);
	spec->headset_amp_left = snd_hda_codec_read(codec, 0x07, 0,
			AC_VERB_GET_AMP_GAIN_MUTE, AC_AMP_GET_INPUT | AC_AMP_GET_LEFT | 1);
	spec->headset_amp_right = snd_hda_codec_read(codec, 0x07, 0,
			AC_VERB_GET_AMP_GAIN_MUTE, AC_AMP_GET_INPUT | AC_AMP_GET_RIGHT | 1);
	spec->headset_active = true;
	snd_hda_codec_write(codec, 0x07, 0, AC_VERB_SET_POWER_STATE, AC_PWRST_D0);
	snd_hda_codec_write(codec, 0x18, 0, AC_VERB_SET_POWER_STATE, AC_PWRST_D0);
	snd_hda_codec_write(codec, 0x07, 0, AC_VERB_SET_CONNECT_SEL, 1);
	/* Unity ADC gain; leave the headset preamp's default unchanged. */
	snd_hda_codec_write(codec, 0x07, 0, AC_VERB_SET_AMP_GAIN_MUTE,
		AC_AMP_SET_INPUT | AC_AMP_SET_LEFT | AC_AMP_SET_RIGHT |
		(1 << AC_AMP_SET_INDEX_SHIFT) | 0x33);
	snd_hda_codec_write(codec, 0x18, 0, AC_VERB_SET_PIN_WIDGET_CONTROL,
			    PIN_IN | mb81_headset_bias);
	snd_hda_codec_setup_stream(codec, 0x07, stream_tag, 0, format);
	mb81_headset_snapshot(codec, "after setup");
	codec_info(codec, "MacBook8,1 headset prepared: ADC=7 bias=%u clock=0x%x\n",
		   mb81_headset_bias, mb81_headset_clock(codec));
	return 0;
}

static int mb81_headset_cleanup(struct hda_pcm_stream *hinfo,
		struct hda_codec *codec, struct snd_pcm_substream *substream)
{
	mb81_headset_restore(codec);
	return 0;
}

static const struct hda_pcm_stream mb81_headset_capture = {
	.substreams = 1,
	.channels_min = 2,
	.channels_max = 2,
	.nid = 0x07,
	.rates = SNDRV_PCM_RATE_44100,
	.formats = SNDRV_PCM_FMTBIT_S16_LE,
	.maxbps = 16,
	.ops = {
		.prepare = mb81_headset_prepare,
		.cleanup = mb81_headset_cleanup,
		.close = mb81_headset_cleanup,
	},
};
