# Changelog

## [1.7.0](https://github.com/shinybrar/skaha/compare/v1.6.1...v1.7.0) (2025-05-28)


### Features

* **session:** added session.events to show deployment events on the cluster, e.g. loading container image etc ([58e9bca](https://github.com/shinybrar/skaha/commit/58e9bca90652ffcbcca8eeaecf351123254d62c0))


### Bug Fixes

* **security:** improvements to assertion checks ([2ea1108](https://github.com/shinybrar/skaha/commit/2ea11088d2879918d653dd1c7bd8eaf2ceff24d6))
* **security:** X509 certs are checked if valid before first conn. to server ([08327a9](https://github.com/shinybrar/skaha/commit/08327a9ea233ed67084f5a1fd6347f919111aea5))
* **session:** events now returns None, when verbose=True ([1b01dd6](https://github.com/shinybrar/skaha/commit/1b01dd6cfb5972d6476a297679f341e6b00e1bd2))
* **session:** improved docs, better testing logic to await async sleep ([e54b9af](https://github.com/shinybrar/skaha/commit/e54b9af2e011692250e11efb1abf0be6ce53e40b))


### Documentation

* **events:** added session.events docs ([7540062](https://github.com/shinybrar/skaha/commit/7540062a53f480555c8e38253a34d2dd6c8484db))
* **session:** docstring ([7189052](https://github.com/shinybrar/skaha/commit/7189052f0727ed5937072bb56d6942bf54583fd3))

## [1.6.1](https://github.com/shinybrar/skaha/compare/v1.6.0...v1.6.1) (2025-05-22)


### Bug Fixes

* **cleanup:** comments ([8a1a078](https://github.com/shinybrar/skaha/commit/8a1a0785232c404b5b0b68cbd4b8b0349d09a34c))
* **gha:** fix for gh-pages push ([27aa8f8](https://github.com/shinybrar/skaha/commit/27aa8f816575d41b060aec947b8824ee5322f25b))
* Implement httpx error logging hooks and client integration ([fee71c2](https://github.com/shinybrar/skaha/commit/fee71c287a7970cfad1f3db3cd1f12766f716fe1))
* **pre-commit:** cleanup ([abb0839](https://github.com/shinybrar/skaha/commit/abb083980a90018d244ce0e4a91ecc363597f2e4))
* **security:** restricting ssl context to use TLSv1.2 at a minimum ([09654d0](https://github.com/shinybrar/skaha/commit/09654d01d4fbd3092930fa82ef87d504ca4583c0))

## [1.6.0](https://github.com/shinybrar/skaha/compare/v1.5.2...v1.6.0) (2025-05-12)


### Features

* **client:** added loglevel to configure the python logging levels ([431f46d](https://github.com/shinybrar/skaha/commit/431f46dd4abebff53edb1485a5d5064ef432f3bf))
* **client:** added token support to skaha client ([6c7c748](https://github.com/shinybrar/skaha/commit/6c7c7486b6a078a77b5a6b42e2c8162d95ff80f7))
* **client:** updated skaha client to use httpx instead of requests ([4c10de8](https://github.com/shinybrar/skaha/commit/4c10de87451e9687fe29c17f363e5736b36e8203))
* **logs:** added stdout for printing logs in terminal ([0c34cad](https://github.com/shinybrar/skaha/commit/0c34cada7fee945d710727222b27e17e7d46bd06))
* **sessions:** added skaha AsyncSession ([2693272](https://github.com/shinybrar/skaha/commit/26932724e4533bf1823cfad97e3b9ccc8ef5fd7b))
* **sessions:** added support for firefly ([87d16c1](https://github.com/shinybrar/skaha/commit/87d16c1637d5848fbc522c3340c611df40f6d2fa))


### Bug Fixes

* **api:** updated context, images, overview with httpx ([391e857](https://github.com/shinybrar/skaha/commit/391e85732dc324b1d2dee51c4d46d558e5d7d72f))
* **client:** changed to the default and max values of parallel conns ([ce552bf](https://github.com/shinybrar/skaha/commit/ce552bff74602c3525154a5ef4308d9291e9cc53))
* **client:** deprecated client.verify since it no longer affects any logic ([9eed6e9](https://github.com/shinybrar/skaha/commit/9eed6e95db5eadc45ed084bde5eab1cdab7ca727))
* **client:** fixed annotation issues for client, asyncClient ([889a6a8](https://github.com/shinybrar/skaha/commit/889a6a8f9072cf663c10d648248e0a2928ba8873))
* **models:** models no longer search for SKAHA_REGISTRY_[USERNAME|SECRET] from environ, this will be supported in future releases with a comprehensive environment variable support accross all configurable variables ([a1702c9](https://github.com/shinybrar/skaha/commit/a1702c90c1b735ab329b7eedbdabc5811a0eb915))
* **models:** updated checks for session kind ([a8317f4](https://github.com/shinybrar/skaha/commit/a8317f41fa7f59b50d9fb0f7b52bb0a1aafc117d))
* **session:** fixed sync log output when verbose is True ([6ac63f9](https://github.com/shinybrar/skaha/commit/6ac63f9e1a13d7c31d3e0626ae638bb40ed27650))
* **session:** solidified the skaha async session api, moved common query building logic to utils.build ([3f11aee](https://github.com/shinybrar/skaha/commit/3f11aeea5b8ea3617a7d6eed4b4d86863ce4f856))


### Documentation

* **asyncSession:** added docs ([a8be7fc](https://github.com/shinybrar/skaha/commit/a8be7fc540c35f85d24b16f233ef46107302ac5a))
* **client:** updated class docstring ([5531c6f](https://github.com/shinybrar/skaha/commit/5531c6f3794312a1fac64ffbed2f4e20033803c2))
* **index:** typo fixes ([bc637c5](https://github.com/shinybrar/skaha/commit/bc637c5b0e8e05b17d768e8a7cb7b9fb9dd766ab))
* **index:** updates ([a3c2e2e](https://github.com/shinybrar/skaha/commit/a3c2e2e12a9d6311f0a7541c2293749df52138bc))
* **session:** updated docs for session and async sessions ([7e49fef](https://github.com/shinybrar/skaha/commit/7e49fef963dd536b2592b73b9c8d091cf0668984))
* **updates:** docs ([c61fecd](https://github.com/shinybrar/skaha/commit/c61fecd574dc0db2e7a8b36120b5539416b6bdbe))
* **updates:** site config + token support ([54d6ed9](https://github.com/shinybrar/skaha/commit/54d6ed92285a44421450e1139d5f22e62c863694))

## [1.5.2](https://github.com/shinybrar/skaha/compare/v1.5.1...v1.5.2) (2025-03-03)


### Bug Fixes

* **session:** fixed kind translation for session.create, increased max replicas limit to 512 ([9bfe357](https://github.com/shinybrar/skaha/commit/9bfe3575fb78209df546886d08654874799c7b07))

## [1.5.1](https://github.com/shinybrar/skaha/compare/v1.5.0...v1.5.1) (2025-02-26)


### Bug Fixes

* **models:** createSpec model now outputs kind with alias type ([3184d5c](https://github.com/shinybrar/skaha/commit/3184d5c8df740d04b652fa94282682de9084b8d3))

## [1.5.0](https://github.com/shinybrar/skaha/compare/v1.4.4...v1.5.0) (2024-11-22)


### Features

* **context:** updates to context.resources api ([4d08876](https://github.com/shinybrar/skaha/commit/4d08876de0b49201ddef0b8c9ddc01f022fcf11f))


### Bug Fixes

* **docker:** fix for docker build due to uv path install changes ([00fd5de](https://github.com/shinybrar/skaha/commit/00fd5de260793d00b33d65216058c94854e73133))


### Documentation

* **style:** updates ([e886d77](https://github.com/shinybrar/skaha/commit/e886d77253d9b52f43bd5ab3d4c826b1d8a591c3))

## [1.4.4](https://github.com/shinybrar/skaha/compare/v1.4.3...v1.4.4) (2024-11-22)


### Bug Fixes

* **session:** fixed set env in session.create ([00b67ac](https://github.com/shinybrar/skaha/commit/00b67ac1c834439596e481e0a5db17c33f9d7290))

## [1.4.3](https://github.com/shinybrar/skaha/compare/v1.4.2...v1.4.3) (2024-11-08)


### Bug Fixes

* **models:** create.spec model used in session.create now expects env to be None by default ([c34b110](https://github.com/shinybrar/skaha/commit/c34b110fba0e8a84d5e811bc55060fb7a370f6b5))

## [1.4.2](https://github.com/shinybrar/skaha/compare/v1.4.1...v1.4.2) (2024-10-30)


### Bug Fixes

* **models:** added logging ([514fda2](https://github.com/shinybrar/skaha/commit/514fda226a5167ed200b63f0e0bfab06901f4683))


### Documentation

* **index:** updated the landing page ([e7dbac2](https://github.com/shinybrar/skaha/commit/e7dbac2049e4bc9e24886c83d1d971c04119c0a8))

## [1.4.1](https://github.com/shinybrar/skaha/compare/v1.4.0...v1.4.1) (2024-10-25)


### Bug Fixes

* **github-actions:** added path restrictions for workflow triggers, reduced permissions for build flows ([1220765](https://github.com/shinybrar/skaha/commit/12207651d6f901ec4bd1820cfeb5f3cdf7edb0a1))
* **pyproject:** fixed toml file with bad license key ([ac1ffb6](https://github.com/shinybrar/skaha/commit/ac1ffb620ae4fbfabcbd5c136f192d56949ba29b))

## [1.4.0](https://github.com/shinybrar/skaha/compare/v1.3.1...v1.4.0) (2024-10-25)


### Features

* **build:** added edge container build and attestation ([d07e008](https://github.com/shinybrar/skaha/commit/d07e008dd8c4de36a8e20ca50f5a91dc03f8afd4))
* **codecov:** added badge ([373412d](https://github.com/shinybrar/skaha/commit/373412d8f8b6a806b111a5d8dac89c64a876d6b3))
* **conduct:** added a code of conduct for skaha community ([f37046e](https://github.com/shinybrar/skaha/commit/f37046e4baab6fe83eb00a64e004772d89b8bea2))
* **contributions:** added a guideline ([271a6df](https://github.com/shinybrar/skaha/commit/271a6df3a4d3417991488a3571181941be7ae9ce))
* **dockerfile:** added base dockerfile for the project ([28f7e51](https://github.com/shinybrar/skaha/commit/28f7e5120d500081c44083f1141eeeacf89e1305))
* **docs:** added conduct,contributing,license and security sections to docs ([5cac3c0](https://github.com/shinybrar/skaha/commit/5cac3c0d385564afd27b6d74dd139dd1162a8ae7))
* **github-actions:** added pypi release action and updated client payload ([b0b3593](https://github.com/shinybrar/skaha/commit/b0b3593d7166559032de099cf829a96203126f78))
* **license:** project now uses the AGPLv3 license ([706f6f8](https://github.com/shinybrar/skaha/commit/706f6f8afa0b649a316a7f77de08571fe22b0e8a))
* **module:** added support for private container registries ([3b47c5c](https://github.com/shinybrar/skaha/commit/3b47c5cee4fb5838efb87b9d17a9f7cd6da3d629))
* **packaging:** moved skaha from poetry backend to uv ([3b7b89f](https://github.com/shinybrar/skaha/commit/3b7b89fb508d261ea83df269349142be44089abd))
* **security:** added a security policy for the project ([1338e7f](https://github.com/shinybrar/skaha/commit/1338e7fecb1855192c414a2ba80c02775a75b86b))
* **security:** ossf scorecard ([719cdfc](https://github.com/shinybrar/skaha/commit/719cdfccb68f96eea509ae749cb9dd6fc7c0ba9e))
* **session:** added new feature to delete sessions with name prefix, kind and status ([056254b](https://github.com/shinybrar/skaha/commit/056254b9143daa2721486b801093598f1dbc7baa)), closes [#37](https://github.com/shinybrar/skaha/issues/37)
* **templates:** added bug report and feature requests templates ([8a8dd20](https://github.com/shinybrar/skaha/commit/8a8dd205bebda814902f66cc39924b7280d817dc))


### Bug Fixes

* **attestation:** added attestation for dockerhub container image ([0ff4ba2](https://github.com/shinybrar/skaha/commit/0ff4ba2b321d61483325018d42f39c97d22eb3cb))
* **badge:** update to codeql bagde url ([c95b6e0](https://github.com/shinybrar/skaha/commit/c95b6e075c8c81f079bca7936940da01645f04a7))
* **ci/cd:** bugfixes ([b4b153c](https://github.com/shinybrar/skaha/commit/b4b153c5dbd92d127fb2ce6a6ac17bdf697b5cb7))
* **ci/cd:** fix for docs build ([98eea9b](https://github.com/shinybrar/skaha/commit/98eea9b1c7a363fbfea4fef42a572af73df7f63d))
* **ci/cd:** fixes for action deprecations, and uv errors ([6a5af8c](https://github.com/shinybrar/skaha/commit/6a5af8c5174f89f23ccd5ae490f0850761275f6f))
* **CI:** change to pre-commit checks ([6216b02](https://github.com/shinybrar/skaha/commit/6216b0279b14e7d716e01f7f9782405ecb9244ca))
* **ci:** ci indent fix ([4e02f72](https://github.com/shinybrar/skaha/commit/4e02f7258a51493fcaef6cf52817ce6799eb8cd7))
* **ci:** fix to edge container build ([59924bd](https://github.com/shinybrar/skaha/commit/59924bd8193f609ec2e958eea59a333469d41de3))
* **ci:** improved secret cleanup ([990c5a1](https://github.com/shinybrar/skaha/commit/990c5a1e461843db681417bb229bcb51c13d8aed))
* **contribution:** updated guidelines ([bc5400e](https://github.com/shinybrar/skaha/commit/bc5400e9b2901d76a53c502d10688bf7f9361dfa))
* **dockerfile:** fix to stage names ([f46b081](https://github.com/shinybrar/skaha/commit/f46b081dc6d9e7013e23f99e5e4e41e755dac81a))
* **docs/ci:** small fixes ([e92c9eb](https://github.com/shinybrar/skaha/commit/e92c9eb004d3517a3f639b5c84fbc8eb8e7fa27c))
* **docs:** updated doc/status/badge links ([6efed00](https://github.com/shinybrar/skaha/commit/6efed008e292c557cbf44f7f1c3ca2113f3d14af))
* **github-actions:** added fixes for release deployments ([dc1b03d](https://github.com/shinybrar/skaha/commit/dc1b03d5151f9b839eceb0ff616004efc729fa38))
* **github-actions:** possible fix for deployment action ([41e1886](https://github.com/shinybrar/skaha/commit/41e1886e200a93f23b251259cf7b25192baa5445))
* **github-actions:** release actions now checkout tag_name ref for code ([ebffafe](https://github.com/shinybrar/skaha/commit/ebffafe6d11149d8fc05b9a4787dce16923f9c76))
* **readme:** codeql bagde url ([197a6eb](https://github.com/shinybrar/skaha/commit/197a6eb2ccbcb1451d5ce0fd15672e80dd9d87d6))
* **tests:** debugging ci/cd and common errors ([7d6b3a9](https://github.com/shinybrar/skaha/commit/7d6b3a979d0436acb4a9914d988f03e6a797b552))
* **tests:** fixed issue with session tests ([d004fde](https://github.com/shinybrar/skaha/commit/d004fde6b9cf17cf49bac833151d2fc5945486d6))
* **tests:** fixed issues with codecov tokens ([07f87d9](https://github.com/shinybrar/skaha/commit/07f87d984959501329dcca1e6ee7ed83f14c3f1a))
* **tests:** fixed session tests to be more consistent and run ~60s ([19f0a6e](https://github.com/shinybrar/skaha/commit/19f0a6e00414bdd883ae699de1fb4edac5f5fba7))
* **tests:** fixed threading issue caused when one of the futures timesout ([ba55a38](https://github.com/shinybrar/skaha/commit/ba55a380ab5f8bd9c06e34a9c6cf543ea4ec7923))
* **tests:** fixes for session tests ([b3f3e48](https://github.com/shinybrar/skaha/commit/b3f3e4813953bc31e58c864f1f36f70a53bdac41))
* **typing:** multiple type hint fixes throughout the project ([a533481](https://github.com/shinybrar/skaha/commit/a53348166f8573af8c9780ded4a08f0fe95d6e44))
* **utils:** fixed logging x2 issue ([7e218df](https://github.com/shinybrar/skaha/commit/7e218df82d7b97087a84ad8ea0ee621a029363e3))


### Documentation

* **github-actions:** changed the workflow name ([868e114](https://github.com/shinybrar/skaha/commit/868e1147e7a32c69d92cc325db7b3074feeace31))
* **README:** updated with CI status ([175ffce](https://github.com/shinybrar/skaha/commit/175ffcecdeb6e89f45c078180b732f22890b6403))
* **sessions:** added docs for destroy_with fucntionality ([afd0a11](https://github.com/shinybrar/skaha/commit/afd0a1115dfd10535aa9cee9decda22136f6f10f))
* **skaha:** updated all docs ([04551c9](https://github.com/shinybrar/skaha/commit/04551c925320cc7bc068f554705975f2c429f4a5))

## [1.3.1](https://github.com/CHIMEFRB/skaha/compare/v1.3.0...v1.3.1) (2023-11-15)


### Bug Fixes

* **docs:** updated docs to include changelog, added reference for calling gpus in session.create ([e58f9be](https://github.com/CHIMEFRB/skaha/commit/e58f9be5ae07264bd8046d1980a742c4124d34a1))

## [1.3.0](https://github.com/CHIMEFRB/skaha/compare/v1.2.0...v1.3.0) (2023-11-14)


### Features

* **docs:** updates with a new ability to edit docs via PR ([aa2314d](https://github.com/CHIMEFRB/skaha/commit/aa2314d9f57778e7328f1c9f2fd64470a76af66b))


### Bug Fixes

* **docs:** updated readme ([4b81e7e](https://github.com/CHIMEFRB/skaha/commit/4b81e7ebfb0d86f50153edb07e9cf536a02ea802))

## [1.2.0](https://github.com/CHIMEFRB/skaha/compare/v1.1.1...v1.2.0) (2023-06-08)


### Features

* **client:** updated client to include skaha version in prep for v1 release ([e6360c0](https://github.com/CHIMEFRB/skaha/commit/e6360c07d9b305463e00f2f8293e6c9a2dc83f42))
* **overview:** added new overview module ([4a6336f](https://github.com/CHIMEFRB/skaha/commit/4a6336ff9d1ff3e05701848a500d35585cb0b154))


### Bug Fixes

* **deps:** updates ([5644e15](https://github.com/CHIMEFRB/skaha/commit/5644e15c5b28de2a54be2607d87ca2a3439e7659))
* **session:** fix for spawning sessions with gpus ([961f766](https://github.com/CHIMEFRB/skaha/commit/961f76673783f948a6cf0c3c2b70bb34e4d6d853))
* **tests:** fixed session tests, which now default spawn with name-{replica-id} format ([7e48031](https://github.com/CHIMEFRB/skaha/commit/7e48031281e5ed1e35b891655769977aa4d3fc44))

## [1.1.1](https://github.com/CHIMEFRB/skaha/compare/v1.1.0...v1.1.1) (2022-12-16)


### Documentation

* **readme:** update ([1b975b6](https://github.com/CHIMEFRB/skaha/commit/1b975b67da82a68d8c5072cc5739dcd024f39584))

## [1.1.0](https://github.com/CHIMEFRB/skaha/compare/v1.0.2...v1.1.0) (2022-12-16)


### Features

* **docs:** added build ([9049b92](https://github.com/CHIMEFRB/skaha/commit/9049b92b211bf4081b07f397a1c62ce058f3183b))
* **session:** create session now embeds two env variables into the container, REPLICA_COUNT and REPLICA_ID ([ecbf48a](https://github.com/CHIMEFRB/skaha/commit/ecbf48ad19536945f2359e75d0c3482a2e77feee))


### Bug Fixes

* **docs:** build command issue ([becbc60](https://github.com/CHIMEFRB/skaha/commit/becbc60fb605dd832a90b6b5e5941ce07dc092b6))
* **docs:** fixed build issue ([98b0543](https://github.com/CHIMEFRB/skaha/commit/98b0543f933087cac63955c40dd424285f70656f))

## [1.0.2](https://github.com/CHIMEFRB/skaha/compare/v1.0.1...v1.0.2) (2022-12-15)


### Bug Fixes

* **docs:** created documentation for the project ([e0f5483](https://github.com/CHIMEFRB/skaha/commit/e0f5483c2c72cd489258a84e3cb06d142a06f4da))


### Documentation

* **API-Reference:** changed where order of docs ([569d34f](https://github.com/CHIMEFRB/skaha/commit/569d34f00747fd1d2eff8f997ae277b63080df50))

## [1.0.1](https://github.com/CHIMEFRB/skaha/compare/v1.0.0...v1.0.1) (2022-12-15)


### Bug Fixes

* **env:** fixed multiple tests and added support for multiple env parameters ([c0500bf](https://github.com/CHIMEFRB/skaha/commit/c0500bf9c49a359f0b45205a5d1d6524144940f1))

## [1.0.0](https://github.com/CHIMEFRB/skaha/compare/v0.5.0...v1.0.0) (2022-12-14)


### ⚠ BREAKING CHANGES

* **session:** this is a signficant change, breaking all backwards compatibility
* **sessions:** skaha sessions api is no longer supported, the capability to manage multiple sessions is now provided by default with the skaha.session api itself

### Features

* **session:** added support for multiple session management ([219b74c](https://github.com/CHIMEFRB/skaha/commit/219b74cefc99264aca8f041a625dea30325c1f0d))
* **sessions:** skaha.sessions api deprecated ([e184663](https://github.com/CHIMEFRB/skaha/commit/e18466330e67a1b714da86062c79710fd459fa39))


### Bug Fixes

* **client:** updated session header to have the correct content-type ([3146e41](https://github.com/CHIMEFRB/skaha/commit/3146e418b6e075edcd5e34dd03e5b94879b17c08))
* **images:** images api now always prunes ([a436e21](https://github.com/CHIMEFRB/skaha/commit/a436e21085f00e5f6e5a408b1ff0bc486c6881f4))
* **pre-commit:** fixed broken pre-commit config ([baedb82](https://github.com/CHIMEFRB/skaha/commit/baedb825a63efca35573d064836b0928e2579029))
* **type-hints:** fixed broken hints ([9f4e9db](https://github.com/CHIMEFRB/skaha/commit/9f4e9dbba8a923d19e5e180f291c7ff216db9c64))
* **type-hints:** fixed broken type hints ([c1d1356](https://github.com/CHIMEFRB/skaha/commit/c1d1356bbba6642bb86e12b1aaf553094e83ea04))

## [0.5.0](https://github.com/CHIMEFRB/skaha/compare/v0.4.1...v0.5.0) (2022-12-14)


### Features

* **release-please:** implemented ([2ac9728](https://github.com/CHIMEFRB/skaha/commit/2ac972870d84876a74c7631f8af5cad453fab81e))


### Bug Fixes

* **gha:** fix to release action ([cc7b61a](https://github.com/CHIMEFRB/skaha/commit/cc7b61a472da50463f3159aac46f6aa3ae49e79c))
