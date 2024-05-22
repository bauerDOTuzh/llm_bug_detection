// -x-
/*
 * Licensed to Crate.io GmbH ("Crate") under one or more contributor
 * license agreements.  See the NOTICE file distributed with this work for
 * additional information regarding copyright ownership.  Crate licenses
 * this file to you under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.  You may
 * obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  See the
 * License for the specific language governing permissions and limitations
 * under the License.
 *
 * However, if you have executed another commercial license agreement
 * with Crate these terms will supersede the license and you may use the
 * software solely pursuant to the terms of the relevant commercial agreement.
 */

package io.crate.execution.engine.collect.files;

import io.crate.execution.engine.export.FileOutputFactory;
import io.crate.execution.engine.export.LocalFsFileOutputFactory;
import io.crate.plugin.CopyPlugin;
import org.elasticsearch.common.inject.AbstractModule;
import org.elasticsearch.common.inject.multibindings.MapBinder;

import java.util.List;

public class CopyModule extends AbstractModule {

    List<CopyPlugin> copyPlugins;

    public CopyModule(List<CopyPlugin> copyPlugins) {
        this.copyPlugins = copyPlugins;
    }

    @Override
    protected void configure() {
        MapBinder<String, FileInputFactory> fileInputFactoryMapBinder = MapBinder.newMapBinder(binder(), String.class, FileInputFactory.class);
        MapBinder<String, FileOutputFactory> fileOutputFactoryMapBinder = MapBinder.newMapBinder(binder(), String.class, FileOutputFactory.class);

        fileInputFactoryMapBinder.addBinding(LocalFsFileInputFactory.NAME).to(LocalFsFileInputFactory.class).asEagerSingleton();
        fileOutputFactoryMapBinder.addBinding(LocalFsFileOutputFactory.NAME).to(LocalFsFileOutputFactory.class).asEagerSingleton();

        for (var copyPlugin : copyPlugins) {
            for (var e : copyPlugin.getFileInputFactories().entrySet()) {
                fileInputFactoryMapBinder.addBinding(e.getKey()).toInstance(e.getValue());
            }
            for (var e : copyPlugin.getFileOutputFactories().entrySet()) {
                fileOutputFactoryMapBinder.addBinding(e.getKey()).toInstance(e.getValue());
            }
        }
    }
}

//-x-
/*
 * Licensed to Crate.io GmbH ("Crate") under one or more contributor
 * license agreements.  See the NOTICE file distributed with this work for
 * additional information regarding copyright ownership.  Crate licenses
 * this file to you under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.  You may
 * obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  See the
 * License for the specific language governing permissions and limitations
 * under the License.
 *
 * However, if you have executed another commercial license agreement
 * with Crate these terms will supersede the license and you may use the
 * software solely pursuant to the terms of the relevant commercial agreement.
 */

package io.crate.execution.engine.collect.files;

import java.io.IOException;
import java.io.InputStream;
import java.net.URI;
import java.util.List;

public interface FileInput {

    /**
     * this method returns all files that are found within fileUri
     *
     * @return a list of Uris
     * @throws IOException
     */
    List<URI> expandUri() throws IOException;

    InputStream getStream(URI uri) throws IOException;

    boolean isGlobbed();

    URI uri();

    boolean sharedStorageDefault();
}
//-x-
/*
 * Licensed to Crate.io GmbH ("Crate") under one or more contributor
 * license agreements.  See the NOTICE file distributed with this work for
 * additional information regarding copyright ownership.  Crate licenses
 * this file to you under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.  You may
 * obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  See the
 * License for the specific language governing permissions and limitations
 * under the License.
 *
 * However, if you have executed another commercial license agreement
 * with Crate these terms will supersede the license and you may use the
 * software solely pursuant to the terms of the relevant commercial agreement.
 */

package io.crate.execution.engine.collect.files;


import java.util.regex.PatternSyntaxException;

/**
 * This is a copy of sun.nio.fs.Globs to make the methods public available.
 */
public class Globs {
    private Globs() {
    }

    private static final String REGEX_META_CHARS = ".^$+{[]|()";
    private static final String GLOB_META_CHARS = "\\*?[{";

    private static boolean isRegexMeta(char c) {
        return REGEX_META_CHARS.indexOf(c) != -1;
    }

    private static boolean isGlobMeta(char c) {
        return GLOB_META_CHARS.indexOf(c) != -1;
    }

    private static char EOL = 0;  //TBD

    private static char next(String glob, int i) {
        if (i < glob.length()) {
            return glob.charAt(i);
        }
        return EOL;
    }

    /**
     * Creates a regex pattern from the given glob expression.
     *
     * @throws PatternSyntaxException
     */
    private static String toRegexPattern(String globPattern, boolean isDos) {
        boolean inGroup = false;
        StringBuilder regex = new StringBuilder("^");

        int i = 0;
        while (i < globPattern.length()) {
            char c = globPattern.charAt(i++);
            switch (c) {
                case '\\':
                    // escape special characters
                    if (i == globPattern.length()) {
                        throw new PatternSyntaxException("No character to escape",
                            globPattern, i - 1);
                    }
                    char next = globPattern.charAt(i++);
                    if (isGlobMeta(next) || isRegexMeta(next)) {
                        regex.append('\\');
                    }
                    regex.append(next);
                    break;
                case '/':
                    if (isDos) {
                        regex.append("\\\\");
                    } else {
                        regex.append(c);
                    }
                    break;
                case '[':
                    // don't match name separator in class
                    if (isDos) {
                        regex.append("[[^\\\\]&&[");
                    } else {
                        regex.append("[[^/]&&[");
                    }
                    if (next(globPattern, i) == '^') {
                        // escape the regex negation char if it appears
                        regex.append("\\^");
                        i++;
                    } else {
                        // negation
                        if (next(globPattern, i) == '!') {
                            regex.append('^');
                            i++;
                        }
                        // hyphen allowed at start
                        if (next(globPattern, i) == '-') {
                            regex.append('-');
                            i++;
                        }
                    }
                    boolean hasRangeStart = false;
                    char last = 0;
                    while (i < globPattern.length()) {
                        c = globPattern.charAt(i++);
                        if (c == ']') {
                            break;
                        }
                        if (c == '/' || (isDos && c == '\\')) {
                            throw new PatternSyntaxException("Explicit 'name separator' in class",
                                globPattern, i - 1);
                        }
                        // TBD: how to specify ']' in a class?
                        if (c == '\\' || c == '[' ||
                            c == '&' && next(globPattern, i) == '&') {
                            // escape '\', '[' or "&&" for regex class
                            regex.append('\\');
                        }
                        regex.append(c);

                        if (c == '-') {
                            if (!hasRangeStart) {
                                throw new PatternSyntaxException("Invalid range",
                                    globPattern, i - 1);
                            }
                            if ((c = next(globPattern, i++)) == EOL || c == ']') {
                                break;
                            }
                            if (c < last) {
                                throw new PatternSyntaxException("Invalid range",
                                    globPattern, i - 3);
                            }
                            regex.append(c);
                            hasRangeStart = false;
                        } else {
                            hasRangeStart = true;
                            last = c;
                        }
                    }
                    if (c != ']') {
                        throw new PatternSyntaxException("Missing ']", globPattern, i - 1);
                    }
                    regex.append("]]");
                    break;
                case '{':
                    if (inGroup) {
                        throw new PatternSyntaxException("Cannot nest groups",
                            globPattern, i - 1);
                    }
                    regex.append("(?:(?:");
                    inGroup = true;
                    break;
                case '}':
                    if (inGroup) {
                        regex.append("))");
                        inGroup = false;
                    } else {
                        regex.append('}');
                    }
                    break;
                case ',':
                    if (inGroup) {
                        regex.append(")|(?:");
                    } else {
                        regex.append(',');
                    }
                    break;
                case '*':
                    if (next(globPattern, i) == '*') {
                        // crosses directory boundaries
                        regex.append(".*");
                        i++;
                    } else {
                        // within directory boundary
                        if (isDos) {
                            regex.append("[^\\\\]*");
                        } else {
                            regex.append("[^/]*");
                        }
                    }
                    break;
                case '?':
                    if (isDos) {
                        regex.append("[^\\\\]");
                    } else {
                        regex.append("[^/]");
                    }
                    break;

                default:
                    if (isRegexMeta(c)) {
                        regex.append('\\');
                    }
                    regex.append(c);
            }
        }

        if (inGroup) {
            throw new PatternSyntaxException("Missing '}", globPattern, i - 1);
        }

        return regex.append('$').toString();
    }

    public static String toUnixRegexPattern(String globPattern) {
        return toRegexPattern(globPattern, false);
    }

}
// -x-
/*
 * Licensed to Crate.io GmbH ("Crate") under one or more contributor
 * license agreements.  See the NOTICE file distributed with this work for
 * additional information regarding copyright ownership.  Crate licenses
 * this file to you under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.  You may
 * obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  See the
 * License for the specific language governing permissions and limitations
 * under the License.
 *
 * However, if you have executed another commercial license agreement
 * with Crate these terms will supersede the license and you may use the
 * software solely pursuant to the terms of the relevant commercial agreement.
 */

package io.crate.execution.engine.collect.files;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.util.List;

import io.crate.analyze.CopyFromParserProperties;
import io.crate.data.BatchIterator;
import io.crate.data.Input;
import io.crate.data.MappedForwardingBatchIterator;
import io.crate.data.Row;
import io.crate.execution.dsl.phases.FileUriCollectPhase;
import io.crate.execution.dsl.phases.FileUriCollectPhase.InputFormat;
import io.crate.execution.engine.collect.files.FileReadingIterator.LineCursor;
import io.crate.expression.InputRow;
import io.crate.expression.reference.file.LineContext;
import io.crate.operation.collect.files.CSVLineParser;

public final class LineProcessor extends MappedForwardingBatchIterator<LineCursor, Row> {

    private final BatchIterator<LineCursor> source;
    private final LineContext lineContext;
    private final CopyFromParserProperties parserProperties;
    private final List<String> targetColumns;
    private final InputRow row;

    private InputFormat inputFormat;
    private CSVLineParser csvLineParser;
    private boolean firstLine = true;

    public LineProcessor(BatchIterator<LineCursor> source,
                         List<Input<?>> inputs,
                         List<LineCollectorExpression<?>> expressions,
                         FileUriCollectPhase.InputFormat inputFormat,
                         CopyFromParserProperties parserProperties,
                         List<String> targetColumns) {
        this.source = source;
        this.inputFormat = inputFormat;
        this.row = new InputRow(inputs);
        this.parserProperties = parserProperties;
        this.targetColumns = targetColumns;
        this.lineContext = new LineContext(source.currentElement());
        for (LineCollectorExpression<?> collectorExpression : expressions) {
            collectorExpression.startCollect(lineContext);
        }
    }

    @Override
    public void moveToStart() {
        source.moveToStart();
        firstLine = true;
    }

    private boolean readFirstLine(URI currentUri, String line) throws IOException {
        if (isCSV(inputFormat, currentUri)) {
            csvLineParser = new CSVLineParser(parserProperties, targetColumns);
            inputFormat = InputFormat.CSV;
            if (parserProperties.fileHeader()) {
                csvLineParser.parseHeader(line);
                return true;
            }
        } else {
            inputFormat = InputFormat.JSON;
        }
        return false;
    }

    private byte[] getByteArray(String line, long rowNumber) throws IOException {
        if (inputFormat == InputFormat.CSV) {
            return parserProperties.fileHeader() ?
                csvLineParser.parse(line, rowNumber) : csvLineParser.parseWithoutHeader(line, rowNumber);
        } else {
            return line.getBytes(StandardCharsets.UTF_8);
        }
    }

    private static boolean isCSV(FileUriCollectPhase.InputFormat inputFormat, URI currentUri) {
        return (inputFormat == FileUriCollectPhase.InputFormat.CSV) || currentUri.toString().endsWith(".csv");
    }

    @Override
    public boolean moveNext() {
        try {
            while (source.moveNext()) {
                LineCursor cursor = source.currentElement();
                String line = cursor.line();
                if (line == null) {
                    assert cursor.failure() != null : "If the line is null, there must be a failure";
                    return true;
                }
                if (firstLine) {
                    firstLine = false;
                    if (readFirstLine(cursor.uri(), line)) {
                        continue;
                    }
                }
                try {
                    byte[] json = getByteArray(line, cursor.lineNumber());
                    lineContext.resetCurrentParsingFailure();
                    lineContext.rawSource(json);
                } catch (Throwable parseError) {
                    lineContext.setCurrentParsingFailure(parseError.getMessage());
                }
                return true;
            }
            return false;
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
    }

    @Override
    public Row currentElement() {
        return row;
    }

    @Override
    protected BatchIterator<LineCursor> delegate() {
        return source;
    }
}

// -x-
/*
 * Licensed to Crate.io GmbH ("Crate") under one or more contributor
 * license agreements.  See the NOTICE file distributed with this work for
 * additional information regarding copyright ownership.  Crate licenses
 * this file to you under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.  You may
 * obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  See the
 * License for the specific language governing permissions and limitations
 * under the License.
 *
 * However, if you have executed another commercial license agreement
 * with Crate these terms will supersede the license and you may use the
 * software solely pursuant to the terms of the relevant commercial agreement.
 */

package io.crate.execution.engine.collect.files;


import org.jetbrains.annotations.VisibleForTesting;

import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.URI;
import java.nio.file.AccessDeniedException;
import java.nio.file.FileSystemLoopException;
import java.nio.file.FileVisitResult;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.SimpleFileVisitor;
import java.nio.file.attribute.BasicFileAttributes;
import java.util.ArrayList;
import java.util.EnumSet;
import java.util.List;
import java.util.function.Predicate;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import static io.crate.execution.engine.collect.files.FileReadingIterator.toURI;
import static java.nio.file.FileVisitOption.FOLLOW_LINKS;

public class LocalFsFileInput implements FileInput {

    private static final Pattern HAS_GLOBS_PATTERN = Pattern.compile("^((file://|/)[^\\*]*/)[^\\*]*\\*.*");

    @NotNull
    private final URI uri;
    @Nullable
    @VisibleForTesting
    final URI preGlobUri;
    @NotNull
    private final Predicate<URI> uriPredicate;

    public LocalFsFileInput(URI uri) throws IOException {
        Matcher hasGlobMatcher = HAS_GLOBS_PATTERN.matcher(uri.toString());
        /*
         * hasGlobMatcher.group(1) returns part of the path before the wildcards with a trailing backslash,
         * ex)
         *      'file:///bucket/prefix/*.json'                           -> 'file:///bucket/prefix/'
         *      's3://bucket/year=2020/month=12/day=*0/hour=12/*.json'   -> 's3://bucket/year=2020/month=12/'
         */
        if (hasGlobMatcher.matches()) {
            Path oldPath = Paths.get(toURI(hasGlobMatcher.group(1)));
            String oldPathAsString = oldPath.toUri().toString();
            String newPathAsString = oldPath.toRealPath().toUri().toString();
            String resolvedFileUrl = uri.toString().replace(oldPathAsString, newPathAsString);
            this.uri = toURI(resolvedFileUrl);
            this.preGlobUri = toURI(newPathAsString);
        } else {
            this.uri = uri;
            this.preGlobUri = null;
        }
        this.uriPredicate = new GlobPredicate(this.uri);
    }

    @Override
    public boolean isGlobbed() {
        return preGlobUri != null;
    }

    @Override
    public URI uri() {
        // returns a realPath if it was a symbolic link
        return uri;
    }

    @Override
    public List<URI> expandUri() throws IOException {
        if (preGlobUri == null) {
            return List.of(uri);
        }

        Path preGlobPath = Paths.get(preGlobUri);
        if (!Files.isDirectory(preGlobPath)) {
            preGlobPath = preGlobPath.getParent();
            if (preGlobPath == null) {
                return List.of();
            }
        }
        if (Files.notExists(preGlobPath)) {
            return List.of();
        }
        final int fileURIDepth = countOccurrences(uri.toString(), '/');
        final int maxDepth = fileURIDepth - countOccurrences(preGlobUri.toString(), '/') + 1;
        final List<URI> uris = new ArrayList<>();

        var fileVisitor = new SimpleFileVisitor<Path>() {
            @Override
            public FileVisitResult visitFileFailed(Path file, IOException exc) throws IOException {
                if (exc instanceof AccessDeniedException) {
                    return FileVisitResult.CONTINUE;
                }
                if (exc instanceof FileSystemLoopException) {
                    final int maxDepth = fileURIDepth - countOccurrences(file.toUri().toString(), '/') + 1;
                    if (maxDepth >= 0) {
                        Files.walkFileTree(file, EnumSet.of(FOLLOW_LINKS), maxDepth, this);
                    }
                    return FileVisitResult.CONTINUE;
                }
                throw exc;
            }

            @Override
            public FileVisitResult visitFile(Path file, BasicFileAttributes attrs) {
                URI uri = file.toUri();
                if (uriPredicate.test(uri)) {
                    uris.add(uri);
                }
                return FileVisitResult.CONTINUE;
            }
        };
        Files.walkFileTree(preGlobPath, EnumSet.of(FOLLOW_LINKS), maxDepth, fileVisitor);
        return uris;
    }

    @Override
    public InputStream getStream(URI uri) throws IOException {
        File file = new File(uri);
        return new FileInputStream(file);
    }

    @Override
    public boolean sharedStorageDefault() {
        return false;
    }

    private static int countOccurrences(String str, char c) throws IOException {
        try {
            return Math.toIntExact(str.chars().filter(ch -> ch == c).count());
        } catch (ArithmeticException e) {
            throw new IOException("Provided URI is too long");
        }
    }

    private static class GlobPredicate implements Predicate<URI> {
        private final Pattern globPattern;

        GlobPredicate(URI fileUri) {
            this.globPattern = Pattern.compile(Globs.toUnixRegexPattern(fileUri.toString()));
        }

        @Override
        public boolean test(@Nullable URI input) {
            return input != null && globPattern.matcher(input.toString()).matches();
        }
    }
}

// -x-
/*
 * Licensed to Crate.io GmbH ("Crate") under one or more contributor
 * license agreements.  See the NOTICE file distributed with this work for
 * additional information regarding copyright ownership.  Crate licenses
 * this file to you under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.  You may
 * obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  See the
 * License for the specific language governing permissions and limitations
 * under the License.
 *
 * However, if you have executed another commercial license agreement
 * with Crate these terms will supersede the license and you may use the
 * software solely pursuant to the terms of the relevant commercial agreement.
 */

package io.crate.execution.engine.collect.files;

import io.crate.common.StringUtils;
import io.crate.common.Suppliers;
import io.crate.types.DataTypes;
import org.locationtech.spatial4j.shape.Point;

import org.jetbrains.annotations.Nullable;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.concurrent.TimeUnit;
import java.util.function.Supplier;

public class SummitsIterable implements Iterable<SummitsContext> {

    private final Supplier<List<SummitsContext>> summitsSupplierCache = Suppliers.memoizeWithExpiration(
        this::fetchSummits, 4, TimeUnit.MINUTES
    );

    private List<SummitsContext> fetchSummits() {
        List<SummitsContext> summits = new ArrayList<>();
        try (InputStream input = SummitsIterable.class.getResourceAsStream("/config/names.txt")) {
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(input, StandardCharsets.UTF_8))) {
                String line;
                while ((line = reader.readLine()) != null) {
                    List<String> parts = StringUtils.splitToList('\t', line);
                    summits.add(new SummitsContext(
                        parts.get(0),
                        tryParse(parts.get(1)),
                        tryParse(parts.get(2)),
                        safeParseCoordinates(parts.get(3)),
                        parts.get(4),
                        parts.get(5),
                        parts.get(6),
                        parts.get(7),
                        tryParse(parts.get(8)))
                    );
                }
            }
        } catch (IOException e) {
            throw new RuntimeException("Cannot populate the sys.summits table", e);
        }
        return summits;
    }

    private static Integer tryParse(String string) {
        Long result = null;
        try {
            result = Long.parseLong(string, 10);
        } catch (NumberFormatException e) {
            return null;
        }
        if (result != result.intValue()) {
            return null;
        } else {
            return result.intValue();
        }
    }

    @Nullable
    private static Point safeParseCoordinates(String value) {
        return value.isEmpty() ? null : DataTypes.GEO_POINT.implicitCast(value);
    }

    @Override
    public Iterator<SummitsContext> iterator() {
        return summitsSupplierCache.get().iterator();
    }
}

// -x-
/*
 * Licensed to Crate.io GmbH ("Crate") under one or more contributor
 * license agreements.  See the NOTICE file distributed with this work for
 * additional information regarding copyright ownership.  Crate licenses
 * this file to you under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.  You may
 * obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  See the
 * License for the specific language governing permissions and limitations
 * under the License.
 *
 * However, if you have executed another commercial license agreement
 * with Crate these terms will supersede the license and you may use the
 * software solely pursuant to the terms of the relevant commercial agreement.
 */

package io.crate.execution.engine.collect.files;

import java.io.IOException;
import java.io.InputStream;
import java.net.URI;
import java.net.URL;
import java.util.Collections;
import java.util.List;

class URLFileInput implements FileInput {

    private final URI fileUri;

    public URLFileInput(URI fileUri) {
        // If the full fileUri contains a wildcard the fileUri passed as argument here is the fileUri up to the wildcard
        this.fileUri = fileUri;
    }

    @Override
    public boolean isGlobbed() {
        return false;
    }

    @Override
    public URI uri() {
        return fileUri;
    }

    @Override
    public List<URI> expandUri() throws IOException {
        // for URLs listing directory contents is not supported so always return the full fileUri for now
        return Collections.singletonList(this.fileUri);
    }

    @Override
    public InputStream getStream(URI uri) throws IOException {
        URL url = uri.toURL();
        return url.openStream();
    }

    @Override
    public boolean sharedStorageDefault() {
        return true;
    }
}
// -x-
/*
 * Licensed to Crate.io GmbH ("Crate") under one or more contributor
 * license agreements.  See the NOTICE file distributed with this work for
 * additional information regarding copyright ownership.  Crate licenses
 * this file to you under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.  You may
 * obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  See the
 * License for the specific language governing permissions and limitations
 * under the License.
 *
 * However, if you have executed another commercial license agreement
 * with Crate these terms will supersede the license and you may use the
 * software solely pursuant to the terms of the relevant commercial agreement.
 */

package io.crate.execution.engine.collect;

import java.io.File;
import java.util.Map;

import org.elasticsearch.client.ElasticsearchClient;
import org.elasticsearch.cluster.service.ClusterService;
import org.elasticsearch.common.settings.Settings;
import org.elasticsearch.indices.breaker.CircuitBreakerService;
import org.elasticsearch.threadpool.ThreadPool;
import org.jetbrains.annotations.Nullable;

import io.crate.blob.v2.BlobShard;
import io.crate.common.collections.Lists;
import io.crate.data.BatchIterator;
import io.crate.data.InMemoryBatchIterator;
import io.crate.data.Row;
import io.crate.data.SentinelRow;
import io.crate.execution.dsl.phases.RoutedCollectPhase;
import io.crate.execution.engine.collect.collectors.BlobOrderedDocCollector;
import io.crate.execution.engine.collect.collectors.OrderedDocCollector;
import io.crate.execution.engine.export.FileOutputFactory;
import io.crate.execution.jobs.NodeLimits;
import io.crate.execution.jobs.SharedShardContext;
import io.crate.expression.InputFactory;
import io.crate.expression.reference.doc.blob.BlobReferenceResolver;
import io.crate.expression.reference.sys.shard.ShardRowContext;
import io.crate.metadata.NodeContext;
import io.crate.metadata.Schemas;
import io.crate.metadata.TransactionContext;

public class BlobShardCollectorProvider extends ShardCollectorProvider {

    private final BlobShard blobShard;
    private final InputFactory inputFactory;

    public BlobShardCollectorProvider(BlobShard blobShard,
                                      ClusterService clusterService,
                                      Schemas schemas,
                                      NodeLimits nodeJobsCounter,
                                      CircuitBreakerService circuitBreakerService,
                                      NodeContext nodeCtx,
                                      ThreadPool threadPool,
                                      Settings settings,
                                      ElasticsearchClient elasticsearchClient,
                                      Map<String, FileOutputFactory> fileOutputFactoryMap) {
        super(
            clusterService,
            circuitBreakerService,
            schemas,
            nodeJobsCounter,
            nodeCtx,
            threadPool,
            settings,
            elasticsearchClient,
            blobShard.indexShard(),
            new ShardRowContext(blobShard, clusterService),
            fileOutputFactoryMap
        );
        inputFactory = new InputFactory(nodeCtx);
        this.blobShard = blobShard;
    }

    @Nullable
    @Override
    protected BatchIterator<Row> getProjectionFusedIterator(RoutedCollectPhase normalizedPhase, CollectTask collectTask) {
        return null;
    }

    @Override
    protected BatchIterator<Row> getUnorderedIterator(RoutedCollectPhase collectPhase,
                                                      boolean requiresScroll,
                                                      CollectTask collectTask) {
        return InMemoryBatchIterator.of(getBlobRows(collectTask.txnCtx(), collectPhase, requiresScroll), SentinelRow.SENTINEL,
                                        true);
    }

    private Iterable<Row> getBlobRows(TransactionContext txnCtx, RoutedCollectPhase collectPhase, boolean requiresRepeat) {
        Iterable<File> files = blobShard.blobContainer().getFiles();
        Iterable<Row> rows = RowsTransformer.toRowsIterable(txnCtx, inputFactory, BlobReferenceResolver.INSTANCE, collectPhase, files);
        if (requiresRepeat) {
            return Lists.of(rows);
        }
        return rows;
    }

    public OrderedDocCollector getOrderedCollector(RoutedCollectPhase collectPhase,
                                                   SharedShardContext sharedShardContext,
                                                   CollectTask collectTask,
                                                   boolean requiresRepeat) {
        RoutedCollectPhase normalizedCollectPhase = collectPhase.normalize(shardNormalizer, collectTask.txnCtx());
        return new BlobOrderedDocCollector(
            blobShard.indexShard().shardId(),
            getBlobRows(collectTask.txnCtx(), normalizedCollectPhase, requiresRepeat));
    }
}

// -x-

/*
 * Licensed to Crate.io GmbH ("Crate") under one or more contributor
 * license agreements.  See the NOTICE file distributed with this work for
 * additional information regarding copyright ownership.  Crate licenses
 * this file to you under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.  You may
 * obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  See the
 * License for the specific language governing permissions and limitations
 * under the License.
 *
 * However, if you have executed another commercial license agreement
 * with Crate these terms will supersede the license and you may use the
 * software solely pursuant to the terms of the relevant commercial agreement.
 */

package io.crate.execution.engine.collect;

import java.util.ArrayList;
import java.util.Locale;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionException;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.function.Function;

import org.apache.lucene.search.IndexSearcher;
import org.elasticsearch.Version;
import org.elasticsearch.threadpool.ThreadPool;

import com.carrotsearch.hppc.IntObjectHashMap;

import io.crate.common.annotations.GuardedBy;
import org.jetbrains.annotations.VisibleForTesting;
import io.crate.common.collections.RefCountedItem;
import io.crate.common.exceptions.Exceptions;
import io.crate.data.BatchIterator;
import io.crate.data.Row;
import io.crate.data.RowConsumer;
import io.crate.data.breaker.BlockBasedRamAccounting;
import io.crate.data.breaker.RamAccounting;
import io.crate.execution.dsl.phases.CollectPhase;
import io.crate.execution.dsl.phases.RoutedCollectPhase;
import io.crate.execution.jobs.SharedShardContexts;
import io.crate.execution.jobs.Task;
import io.crate.memory.MemoryManager;
import io.crate.metadata.RowGranularity;
import io.crate.metadata.TransactionContext;


public class CollectTask implements Task {


    private final CollectPhase collectPhase;
    private final TransactionContext txnCtx;
    private final MapSideDataCollectOperation collectOperation;
    private final RamAccounting ramAccounting;
    private final Function<RamAccounting, MemoryManager> memoryManagerFactory;
    private final SharedShardContexts sharedShardContexts;

    private final IntObjectHashMap<RefCountedItem<? extends IndexSearcher>> searchers = new IntObjectHashMap<>();
    private final RowConsumer consumer;
    private final int ramAccountingBlockSizeInBytes;

    @GuardedBy("searchers")
    private final ArrayList<MemoryManager> memoryManagers = new ArrayList<>();
    private final Version minNodeVersion;
    private final CompletableFuture<Void> consumerCompleted;
    private final CompletableFuture<BatchIterator<Row>> batchIterator = new CompletableFuture<>();
    private final AtomicBoolean started = new AtomicBoolean(false);

    @GuardedBy("searchers")
    private boolean releasedResources = false;

    private long totalBytes = -1;

    public CollectTask(CollectPhase collectPhase,
                       TransactionContext txnCtx,
                       MapSideDataCollectOperation collectOperation,
                       RamAccounting ramAccounting,
                       Function<RamAccounting, MemoryManager> memoryManagerFactory,
                       RowConsumer consumer,
                       SharedShardContexts sharedShardContexts,
                       Version minNodeVersion,
                       int ramAccountingBlockSizeInBytes) {
        this.collectPhase = collectPhase;
        this.txnCtx = txnCtx;
        this.collectOperation = collectOperation;
        this.ramAccounting = ramAccounting;
        this.memoryManagerFactory = memoryManagerFactory;
        this.sharedShardContexts = sharedShardContexts;
        this.consumer = consumer;
        this.ramAccountingBlockSizeInBytes = ramAccountingBlockSizeInBytes;
        this.minNodeVersion = minNodeVersion;
        this.batchIterator.whenComplete((it, err) -> {
            if (err == null) {
                try {
                    String threadPoolName = threadPoolName(collectPhase, it.hasLazyResultSet());
                    collectOperation.launch(() -> consumer.accept(it, null), threadPoolName);
                } catch (Throwable t) {
                    consumer.accept(null, t);
                }
            } else {
                consumer.accept(null, err);
            }
        });
        this.consumerCompleted = consumer.completionFuture().handle((res, err) -> {
            totalBytes = ramAccounting.totalBytes();
            releaseResources();
            if (err != null) {
                Exceptions.rethrowUnchecked(err);
            }
            return null;
        });
    }

    private void releaseResources() {
        synchronized (searchers) {
            if (releasedResources == false) {
                releasedResources = true;
                for (var cursor : searchers.values()) {
                    cursor.value.close();
                }
                searchers.clear();
                for (var memoryManager : memoryManagers) {
                    memoryManager.close();
                }
                memoryManagers.clear();
            } else {
                throw new AssertionError("Double release must not happen");
            }
        }
    }

    @Override
    public CompletableFuture<Void> completionFuture() {
        return consumerCompleted;
    }

    @Override
    public void kill(Throwable throwable) {
        if (started.compareAndSet(false, true)) {
            consumer.accept(null, throwable);
        } else {
            batchIterator.whenComplete((it, err) -> {
                if (err == null) {
                    it.kill(throwable);
                } // else: Consumer must have received a failure already
            });
        }
    }

    @Override
    public CompletableFuture<Void> start() {
        if (started.compareAndSet(false, true)) {
            try {
                var futureIt = collectOperation.createIterator(
                    txnCtx,
                    collectPhase,
                    consumer.requiresScroll(),
                    this
                );
                futureIt.whenComplete((it, err) -> {
                    if (err == null) {
                        batchIterator.complete(it);
                    } else {
                        batchIterator.completeExceptionally(err);
                    }
                });
            } catch (Throwable t) {
                batchIterator.completeExceptionally(t);
            }
        }
        return null;
    }

    @Override
    public int id() {
        return collectPhase.phaseId();
    }

    public void addSearcher(int searcherId, RefCountedItem<? extends IndexSearcher> searcher) {
        synchronized (searchers) {
            if (releasedResources == false) {
                var replacedSearcher = searchers.put(searcherId, searcher);
                if (replacedSearcher != null) {
                    replacedSearcher.close();
                    throw new IllegalArgumentException(String.format(Locale.ENGLISH,
                        "ShardCollectContext for %d already added", searcherId));
                }
            } else {
                searcher.close();
                // addSearcher call after resource-release should only happen in error case
                // the join call should trigger the original failure
                try {
                    consumerCompleted.join();
                } catch (CompletionException e) {
                    throw Exceptions.toRuntimeException(e.getCause());
                }
                throw new AssertionError("addSearcher call after resources have already been released once");
            }
        }
    }

    @Override
    public long bytesUsed() {
        if (totalBytes == -1) {
            return ramAccounting.totalBytes();
        } else {
            return totalBytes;
        }
    }

    @Override
    public String name() {
        return collectPhase.name();
    }

    @Override
    public String toString() {
        synchronized (searchers) {
            return "CollectTask{" +
                "id=" + collectPhase.phaseId() +
                ", sharedContexts=" + sharedShardContexts +
                ", consumer=" + consumer +
                ", searchContexts=" + searchers.keys() +
                ", batchIterator=" + batchIterator +
                ", finished=" + consumerCompleted.isDone() +
                '}';
        }
    }

    public TransactionContext txnCtx() {
        return txnCtx;
    }

    public RamAccounting getRamAccounting() {
        // No tracking/close of BlockBasedRamAccounting
        // to avoid double-release of bytes when the parent instance (`ramAccounting`) is closed.
        return new BlockBasedRamAccounting(ramAccounting::addBytes, ramAccountingBlockSizeInBytes);
    }

    public SharedShardContexts sharedShardContexts() {
        return sharedShardContexts;
    }

    @VisibleForTesting
    static String threadPoolName(CollectPhase phase, boolean involvedIO) {
        if (phase instanceof RoutedCollectPhase) {
            RoutedCollectPhase collectPhase = (RoutedCollectPhase) phase;
            if (collectPhase.maxRowGranularity() == RowGranularity.NODE
                       || collectPhase.maxRowGranularity() == RowGranularity.SHARD) {
                // Node or Shard system table collector
                return ThreadPool.Names.GET;
            }
        }
        // If there is no IO involved it is a in-memory system tables. These are usually fast and the overhead
        // of a context switch would be bigger than running this directly.
        return involvedIO ? ThreadPool.Names.SEARCH : ThreadPool.Names.SAME;
    }

    public MemoryManager memoryManager() {
        MemoryManager memoryManager = memoryManagerFactory.apply(ramAccounting);
        // an atomicBoolean call would not be enough, because without syncronization
        // the `memoryManagers.add` could be called just right *after* another thread triggered `releaseResources`
        synchronized (searchers) {
            if (releasedResources == false) {
                memoryManagers.add(memoryManager);
                return memoryManager;
            } else {
                memoryManager.close();
                // memoryManager acess after resource-release should only happen in error case
                // the join call should trigger the original failure
                try {
                    consumerCompleted.join();
                } catch (CompletionException e) {
                    throw Exceptions.toRuntimeException(e.getCause());
                }
                throw new AssertionError("memoryManager access after resources have already been released once");
            }
        }
    }

    public Version minNodeVersion() {
        return minNodeVersion;
    }
}

// -x-
/*
 * Licensed to Crate.io GmbH ("Crate") under one or more contributor
 * license agreements.  See the NOTICE file distributed with this work for
 * additional information regarding copyright ownership.  Crate licenses
 * this file to you under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.  You may
 * obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  See the
 * License for the specific language governing permissions and limitations
 * under the License.
 *
 * However, if you have executed another commercial license agreement
 * with Crate these terms will supersede the license and you may use the
 * software solely pursuant to the terms of the relevant commercial agreement.
 */

package io.crate.execution.engine.collect;

import io.crate.analyze.OrderBy;
import io.crate.execution.dsl.phases.RoutedCollectPhase;
import io.crate.expression.InputFactory;
import io.crate.expression.reference.ReferenceResolver;
import io.crate.expression.reference.doc.lucene.LuceneCollectorExpression;
import io.crate.expression.reference.doc.lucene.OrderByCollectorExpression;
import io.crate.metadata.NodeContext;
import io.crate.metadata.TransactionContext;
import io.crate.types.DataType;

/**
 * Specialized InputFactory for Lucene symbols/expressions.
 *
 * See {@link InputFactory} for an explanation what a InputFactory does.
 */
public class DocInputFactory {

    private final ReferenceResolver<? extends LuceneCollectorExpression<?>> referenceResolver;
    private final InputFactory inputFactory;

    public DocInputFactory(NodeContext nodeCtx,
                           ReferenceResolver<? extends LuceneCollectorExpression<?>> referenceResolver) {
        this.inputFactory = new InputFactory(nodeCtx);
        this.referenceResolver = referenceResolver;
    }

    public InputFactory.Context<? extends LuceneCollectorExpression<?>> extractImplementations(TransactionContext txnCtx,
                                                                                               RoutedCollectPhase phase) {
        OrderBy orderBy = phase.orderBy();
        ReferenceResolver<? extends LuceneCollectorExpression<?>> refResolver;
        if (orderBy == null) {
            refResolver = referenceResolver;
        } else {
            refResolver = ref -> {
                if (orderBy.orderBySymbols().contains(ref)) {
                    DataType<?> dataType = ref.valueType();
                    return new OrderByCollectorExpression(ref, orderBy, dataType::sanitizeValue);
                }
                return referenceResolver.getImplementation(ref);
            };
        }
        InputFactory.Context<? extends LuceneCollectorExpression<?>> ctx = inputFactory.ctxForRefs(txnCtx, refResolver);
        ctx.add(phase.toCollect());
        return ctx;
    }

    public InputFactory.Context<? extends LuceneCollectorExpression<?>> getCtx(TransactionContext txnCtx) {
        return inputFactory.ctxForRefs(txnCtx, referenceResolver);
    }
}

// -x-