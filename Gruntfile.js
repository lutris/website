module.exports = function(grunt) {
  grunt.initConfig({
    pkg: grunt.file.readJSON('package.json'),
    copy: {
      main: {
        files: [
          {
            expand: true,
            flatten: true,
            src: ['components/bootstrap/dist/fonts/*'],
            dest: 'public/fonts/'
          }
        ]
      }
    },
    less: {
      css: {
        options: {
            paths: ['components/bootstrap/less/']
        },
        files: {
          'public/css/lutris.css': ['common_static/css/lutris.less']
        }
      },
      min: {
        options: {
            yuicompress: true,
            paths: ['components/bootstrap/less/']
        },
        files: {
            'public/css/lutris.min.css': ['common_static/css/lutris.less']
        }
      }
    },
    coffee: {
      compile: {
        files: {
          'public/js/app.js': 'common_static/js/*.coffee',
          'public/js/jcrop-fileinput.js': 'components/jcrop-fileinput/src/jcrop-fileinput.coffee'
        }
      }
    },
    concat: {
      css: {
        src: [
          'components/jcrop/css/jquery.Jcrop.css',
          'components/jcrop-fileinput/dist/jcrop-fileinput.css',
          'components/select2/select2.css',
          'components/select2-bootstrap3-css/select2-bootstrap.css'
        ],
        dest: 'public/css/libs.css',
        nonull: true
      },
      js: {
        src: [
          'components/jquery/jquery.js',
          'components/modernizr/modernizr.js',
          'components/bootstrap/dist/js/bootstrap.js',
          'components/jcrop/js/jquery.Jcrop.js',
          'components/jcrop-fileinput/dist/jcrop-fileinput.js',
          'components/select2/select2.js'
        ],
        dest: 'public/js/libs.js',
        nonull: true
      }
    },
    cssmin: {
      dist: {
        files: {
          'public/css/libs.min.css': ['public/css/libs.css']
        }
      }
    },
    uglify: {
      options: {
        banner: '/*! <%= pkg.name %> <%= grunt.template.today("dd-mm-yyyy") %> */\n'
      },
      dist: {
        files: {
          'public/js/libs.min.js': ['public/js/libs.js'],
          'public/js/app.min.js': ['public/js/app.js']
        }
      }
    },
    watch: {
      less: {
        files: 'common_static/css/lutris.less',
        tasks: ['less:css']
      },
      coffee: {
        files: [
          'common_static/js/*.coffee',
          'components/jcrop-fileinput/src/*.coffee'
        ],
        tasks: ['coffee', 'uglify:app']
      },
      templates: {
        files: ['templates/**/*.html']
      }
    },
    browserSync: {
      dev: {
        bsFiles: {
          src: [
            'templates/**',
            'public/**'
          ]
        },
        options: {
          proxy: 'localhost:8000',
          watchTask: true
        }
      }
    }
  });

  grunt.loadNpmTasks('grunt-contrib-copy');
  grunt.loadNpmTasks('grunt-contrib-concat');
  grunt.loadNpmTasks('grunt-contrib-cssmin');
  grunt.loadNpmTasks('grunt-contrib-uglify');
  grunt.loadNpmTasks('grunt-contrib-watch');
  grunt.loadNpmTasks('grunt-browser-sync');
  grunt.loadNpmTasks('grunt-contrib-less');
  grunt.loadNpmTasks('grunt-contrib-coffee');

  grunt.registerTask('default', ['copy', 'less', 'coffee', 'concat', 'cssmin', 'uglify']);
  grunt.registerTask('watch', ['browserSync', 'watch']);
};

