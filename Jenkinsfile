elifePipeline {
    node('containers-jenkins-plugin') {
        def commit

        stage 'Checkout', { checkout scm
            commit = elifeGitRevision()
        }

        stage 'Build images', {
            checkout scm
            // TODO: extract into dockerComposeBuild
            def version
            if (env.TAG_NAME) {
                version = env.TAG_NAME - 'v'
            } else {
                version = 'develop'
            }
            withEnv(["VERSION=${version}"]) {
                dockerComposeBuild(commit)
            }
        }

        stage 'Project tests', {
            try {
                sh "make IMAGE_TAG=${commit} NO_BUILD=y ci-test"
            } finally {
                sh "make ci-clean"
            }
        }

        elifeMainlineOnly {
            stage 'Merge to master', {
                elifeGitMoveToBranch commit, 'master'
            }

            stage 'Push unstable image', {
                def image = DockerImage.elifesciences(this, 'sciencebeam', commit)
                def unstable_image = image.addSuffixAndTag('_unstable', commit)
                unstable_image.tag('latest').push()
                unstable_image.push()
            }

        }

        elifeTagOnly { tagName ->
            def candidateVersion = tagName - "v"

            stage 'Push release image', {
                def image = DockerImage.elifesciences(this, 'sciencebeam', commit)
                image.tag('latest').push()
                image.tag(candidateVersion).push()
            }

            stage 'Downstream', {
                build job: '/dependencies/dependencies-sciencebeam-texture-update-sciencebeam', wait: false, parameters: [string(name: 'tag', value: candidateVersion)]
            }
        }
    }
}
