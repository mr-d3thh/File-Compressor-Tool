# User Guide: Universal Huffman Compressor
This tool is a universal compressor that operates using the Huffman Coding Algorithm. It is capable of compressing and decompressing all file types, including images, PDFs, executables, and text files. The key feature of this tool is that it operates at the byte level, rather than the character level, which allows it to handle any type of data efficiently.
## How it Works with Non-Text Files
Most compression algorithms designed for text rely on the frequency of character repetition. However, when dealing with non-text files—such as images, videos, or executables—this approach is inefficient because these files are not composed of standard characters. Our Huffman compressor is designed to work at the byte level, which offers several advantages:
 1. Handling Any Data Type: Every file is ultimately a sequence of bytes (numbers ranging from 0 to 255). By reading the file byte-by-byte, the algorithm can determine the frequency of each byte regardless of what it represents (a letter, a pixel, or part of an executable code).
 2. Universality: Because it operates at the byte level, this tool is universal and can compress any file type. The Huffman algorithm works on the principle of assigning shorter codes to frequently occurring bytes and longer codes to those that appear less often. This principle applies to any data where bytes have varying frequencies.
 3. Data Integrity (Lossless): The byte-by-byte compression and decompression process ensures that no data is lost. The original file is restored exactly and without any changes after decompression.
## Structure of the Compressed File (.huff Format)
The compressed file (with the .huff extension) has a specific structure that allows for decompression without needing the original file. This structure consists of:
 1. Padding Info (1 byte): This byte specifies the number of extra bits added to the end of the compressed data to ensure it forms a complete byte. This is necessary for reading and writing data accurately byte-by-byte.
 2. Huffman Tree Length (4 bytes): These four bytes define the length of the Huffman tree's bit sequence, helping the decompressor read the tree correctly.
 3. Tree Padding Info (1 byte): Similar to data padding, this byte specifies the number of extra bits added to the end of the Huffman tree's bit sequence.
 4. Huffman Tree: This section is a bit-by-bit representation of the Huffman tree, which is required to reconstruct the Huffman codes during decompression.
 5. Compressed Data: This is the original file data, now compressed using the generated Huffman codes.
## Important Notes
 * Pre-compressed Files: Files that are already compressed (such as **JPG, PNG, MP4, MP3, or ZIP**) may see very little to no reduction in size when processed with this tool. This is because those files already utilize compression algorithms, leaving very little redundancy for the Huffman algorithm to exploit.
 * Size Overhead: In some cases, the compressed file might even be slightly larger than the original if the file is small or already highly optimized, due to the added metadata of the Huffman tree at the beginning of the file.
 * Ideal Use Cases: This tool is highly effective for uncompressed files (such as large text files, BMP images, or WAV audio), where it can significantly reduce the overall file size.
