module.exports = {
  source: ['tokens/**/*.json'],
  platforms: {
    css: {
      transformGroup: 'css',
      buildPath: 'build/css/',
      files: [{
        destination: 'variables.css',
        format: 'css/variables',
        options: {
          outputReferences: true
        }
      }]
    },
    scss: {
      transformGroup: 'scss',
      buildPath: 'build/scss/',
      files: [{
        destination: '_variables.scss',
        format: 'scss/variables'
      }]
    },
    js: {
      transformGroup: 'js',
      buildPath: 'build/js/',
      files: [{
        destination: 'tokens.js',
        format: 'javascript/es6'
      }]
    },
    json: {
      transformGroup: 'js',
      buildPath: 'build/json/',
      files: [{
        destination: 'tokens.json',
        format: 'json/nested'
      }]
    },
    ios: {
      transformGroup: 'ios',
      buildPath: 'build/ios/',
      files: [{
        destination: 'StyleDictionaryColor.h',
        format: 'ios/colors.h',
        className: 'StyleDictionaryColor',
        filter: {
          attributes: {
            category: 'colors'
          }
        }
      }, {
        destination: 'StyleDictionaryColor.m',
        format: 'ios/colors.m',
        className: 'StyleDictionaryColor',
        filter: {
          attributes: {
            category: 'colors'
          }
        }
      }]
    },
    android: {
      transformGroup: 'android',
      buildPath: 'build/android/',
      files: [{
        destination: 'colors.xml',
        format: 'android/colors',
        filter: {
          attributes: {
            category: 'colors'
          }
        }
      }, {
        destination: 'font_dimens.xml',
        format: 'android/fontDimens',
        filter: {
          attributes: {
            category: 'typography'
          }
        }
      }]
    }
  }
};