<template>
  <div>
    <div v-if="noTranslation === true">
      No translation found for this asset
    </div>
    <div
      v-if="isBusy"
      class="wrapper"
    >
      <b-spinner
        variant="secondary"
        label="Loading..."
      />
      <p class="text-muted">
        (Loading...)
      </p>
    </div>
    <div
      v-else-if="noTranslation === false"
      class="wrapper"
    >
      <label>Source Language:</label> {{ source_language }}<br>
      <label>Translated Language:</label> {{ selected_lang_code }}<br>
      <b-form-group>
        <b-form-radio-group
            v-model="translation_url"
            :options="alphabetized_language_collection"
        ></b-form-radio-group>
      </b-form-group>
      <div v-if="translation_url !== ''">
        <a :href="vtt_url">
          <b-button type="button">
            Download VTT
          </b-button>
        </a>
        <br><br>
        {{ getTranslatedText }}
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "Translation",
  data() {
    return {
      vttcaptions: [
        {
          src: "",
          lang: "",
          label: ""
        }
      ],
      translation_url: "",
      target_language: "",
      isBusy: false,
      operator: "translation",
      noTranslation: false,
      num_translations: 0,
      translationsCollection: [
      ],
      selected_lang: "",
      translatedText: "",
      source_language: "",
      translateLanguages: [
        {text: 'Afrikaans', value: 'af'},
        {text: 'Albanian', value: 'sq'},
        {text: 'Amharic', value: 'am'},
        {text: 'Arabic', value: 'ar'},
        {text: 'Azerbaijani', value: 'az'},
        {text: 'Bengali', value: 'bn'},
        {text: 'Bosnian', value: 'bs'},
        {text: 'Bulgarian', value: 'bg'},
        {text: 'Chinese (Simplified)', value: 'zh'},
        // AWS Translate does not support translating from zh to zh-TW
        // {text: 'Chinese (Traditional)', value: 'zh-TW'},
        {text: 'Croatian', value: 'hr'},
        {text: 'Czech', value: 'cs'},
        {text: 'Danish', value: 'da'},
        {text: 'Dari', value: 'fa-AF'},
        {text: 'Dutch', value: 'nl'},
        {text: 'English', value: 'en'},
        {text: 'Estonian', value: 'et'},
        {text: 'Finnish', value: 'fi'},
        {text: 'French', value: 'fr'},
        {text: 'French (Canadian)', value: 'fr-CA'},
        {text: 'Georgian', value: 'ka'},
        {text: 'German', value: 'de'},
        {text: 'Greek', value: 'el'},
        {text: 'Hausa', value: 'ha'},
        {text: 'Hebrew', value: 'he'},
        {text: 'Hindi', value: 'hi'},
        {text: 'Hungarian', value: 'hu'},
        {text: 'Indonesian', value: 'id'},
        {text: 'Italian', value: 'it'},
        {text: 'Japanese', value: 'ja'},
        {text: 'Korean', value: 'ko'},
        {text: 'Latvian', value: 'lv'},
        {text: 'Malay', value: 'ms'},
        {text: 'Norwegian', value: 'no'},
        {text: 'Persian', value: 'fa'},
        {text: 'Pashto', value: 'ps'},
        {text: 'Polish', value: 'pl'},
        {text: 'Portuguese', value: 'pt'},
        {text: 'Romanian', value: 'ro'},
        {text: 'Russian', value: 'ru'},
        {text: 'Serbian', value: 'sr'},
        {text: 'Slovak', value: 'sk'},
        {text: 'Slovenian', value: 'sl'},
        {text: 'Somali', value: 'so'},
        {text: 'Spanish', value: 'es'},
        {text: 'Swahili', value: 'sw'},
        {text: 'Swedish', value: 'sv'},
        {text: 'Tagalog', value: 'tl'},
        {text: 'Tamil', value: 'ta'},
        {text: 'Thai', value: 'th'},
        {text: 'Turkish', value: 'tr'},
        {text: 'Ukrainian', value: 'uk'},
        {text: 'Urdu', value: 'ur'},
        {text: 'Vietnamese', value: 'vi'},
      ]
    }
  },
  computed: {
    alphabetized_language_collection: function() {
      return this.translationsCollection.sort(function(a, b) {
        var textA = a.text.toUpperCase();
        var textB = b.text.toUpperCase();
        return (textA < textB) ? -1 : (textA > textB) ? 1 : 0;
      });
    },
    vtt_url: function() {
      if (this.selected_lang_code !== '') {
        let vttcaption = this.vttcaptions.filter(x => (x.lang === this.selected_lang_code))[0];
        if (vttcaption) {
          return vttcaption.src
        }
      }
    },
    selected_lang_code: function() {
      if (this.selected_lang !== '') {
        return this.translateLanguages.filter(x => (x.text === this.selected_lang))[0].value;
      }
      else {
        return ''
      }
    },
    getTranslatedText: function () {
      let translation = this.translationsCollection.filter(x => (x.value === this.translation_url))[0];
      if (translation) {
        this.selected_lang = translation.text;
      }
      fetch(this.translation_url)
        .then(data => {
          data.text().then((data) => {
            this.translatedText = data
          }).catch(err => console.error(err));
        });
      return this.translatedText
    }
  },
  deactivated: function () {
    console.log('deactivated component:', this.operator)
  },
  activated: function () {
    console.log('activated component:', this.operator);
    this.getTxtTranslations();
    this.getVttCaptions();
  },
  beforeDestroy: function () {
      this.source_language = "";
      this.target_language = "";
    },
  methods: {
    getTxtTranslations: async function () {
      const token = await this.$Amplify.Auth.currentSession().then(data =>{
        return data.getIdToken().getJwtToken();
      });
      this.translationsCollection = [];
      const asset_id = this.$route.params.asset_id;
      fetch(this.DATAPLANE_API_ENDPOINT + '/metadata/' + asset_id + '/TranslateWebCaptions', {
        method: 'get',
        headers: {
          'Authorization': token
        }
      }).then(response => {
        response.json().then(data => ({
            data: data,
          })
        ).then(res => {
          this.num_translations = res.data.results.CaptionsCollection.length;
          res.data.results.CaptionsCollection.forEach(item => {
            const bucket = item.TranslationText.S3Bucket;
            const key = item.TranslationText.S3Key;
            // get URL to captions file in S3
            fetch(this.DATAPLANE_API_ENDPOINT + '/download', {
              method: 'POST',
              mode: 'cors',
              headers: {
                'Content-Type': 'application/json',
                'Authorization': token
              },
              body: JSON.stringify({"S3Bucket": bucket, "S3Key": key})
            }).then(data => {
              data.text().then((data) => {
                let languageLabel = this.translateLanguages.filter(x => (x.value === item.TargetLanguageCode))[0].text;
                this.translationsCollection.push(
                  {text: languageLabel, value: data}
                );
                // set default language selection
                this.translation_url = this.alphabetized_language_collection[0].value
              }).catch(err => console.error(err));
            })
          });
        })
      });
    },
    getVttCaptions: async function () {
      const token = await this.$Amplify.Auth.currentSession().then(data =>{
        return data.getIdToken().getJwtToken();
      });
      const asset_id = this.$route.params.asset_id;

      fetch(this.DATAPLANE_API_ENDPOINT + '/metadata/' + asset_id + '/WebToVTTCaptions', {
        method: 'get',
        headers: {
          'Authorization': token
        }
      }).then(response => {
        response.json().then(data => ({
            data: data,
          })
        ).then(res => {
          let captions_collection = [];
          this.num_caption_tracks = res.data.results.CaptionsCollection.length;
          res.data.results.CaptionsCollection.forEach(item => {
            // TODO: map the language code to a language label
            const bucket = item.Results.S3Bucket;
            const key = item.Results.S3Key;
            // get URL to captions file in S3
            fetch(this.DATAPLANE_API_ENDPOINT + '/download', {
              method: 'POST',
              mode: 'cors',
              headers: {
                'Content-Type': 'application/json',
                'Authorization': token
              },
              body: JSON.stringify({"S3Bucket": bucket, "S3Key": key})
            }).then(data => {
              data.text().then((data) => {
                captions_collection.push({'src': data, 'lang': item.LanguageCode, 'label': item.LanguageCode});
              }).catch(err => console.error(err));
            })
          });
          this.vttcaptions = captions_collection
        })
      });
    },

  }
}
</script>
