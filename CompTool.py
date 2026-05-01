
import heapq
import os
import struct
import tkinter as tk
from tkinter import filedialog, messagebox

class HuffmanNode:
    def __init__(self, byte, freq):
        self.byte = byte
        self.freq = freq
        self.left = None
        self.right = None

    # Used for heapq comparison
    def __lt__(self, other):
        return self.freq < other.freq

class HuffmanCompressor:
    def __init__(self):
        self.huffman_tree = None
        self.huffman_codes = {}
        self.reverse_huffman_codes = {}

    def _build_frequency_table(self, file_path):
        # Initialize frequency table for all 256 possible byte values
        frequency = {i: 0 for i in range(256)}
        with open(file_path, 'rb') as f:
            while True:
                byte_data = f.read(1) # Read one byte at a time
                if not byte_data:
                    break
                byte_value = byte_data[0]
                frequency[byte_value] += 1
        return frequency

    def _build_huffman_tree(self, frequency):
        priority_queue = []
        for byte, freq in frequency.items():
            if freq > 0:
                heapq.heappush(priority_queue, HuffmanNode(byte, freq))

        while len(priority_queue) > 1:
            node1 = heapq.heappop(priority_queue)
            node2 = heapq.heappop(priority_queue)

            merged = HuffmanNode(None, node1.freq + node2.freq)
            merged.left = node1
            merged.right = node2

            heapq.heappush(priority_queue, merged)

        if not priority_queue:
            return None # Handle empty file case
        return priority_queue[0]

    def _build_huffman_codes(self, node, current_code):
        if node is None:
            return

        if node.byte is not None:
            self.huffman_codes[node.byte] = current_code
            self.reverse_huffman_codes[current_code] = node.byte
            return

        self._build_huffman_codes(node.left, current_code + '0')
        self._build_huffman_codes(node.right, current_code + '1')

    def _serialize_huffman_tree(self, node):
        # Pre-order traversal to serialize the tree
        if node.byte is not None:
            return '1' + format(node.byte, '08b') # '1' indicates a leaf node, followed by 8-bit byte value
        else:
            return '0' + self._serialize_huffman_tree(node.left) + self._serialize_huffman_tree(node.right) # '0' indicates an internal node

    def _deserialize_huffman_tree(self, tree_string_iter):
        bit = next(tree_string_iter)
        if bit == '1':
            byte_value = int(''.join(next(tree_string_iter) for _ in range(8)), 2)
            return HuffmanNode(byte_value, 0)
        else:
            node = HuffmanNode(None, 0)
            node.left = self._deserialize_huffman_tree(tree_string_iter)
            node.right = self._deserialize_huffman_tree(tree_string_iter)
            return node

    def compress(self, input_file_path, output_file_path):
        # 1. Build frequency table
        frequency = self._build_frequency_table(input_file_path)
        if all(freq == 0 for freq in frequency.values()):
            raise ValueError("Input file is empty or contains no data.")

        # 2. Build Huffman tree
        self.huffman_tree = self._build_huffman_tree(frequency)
        if self.huffman_tree is None:
            raise ValueError("Could not build Huffman tree (e.g., empty file).")

        # 3. Build Huffman codes
        self.huffman_codes = {}
        self.reverse_huffman_codes = {}
        self._build_huffman_codes(self.huffman_tree, '')

        # 4. Write compressed data to output file
        compressed_data = bytearray()
        bit_buffer = ''
        padding_info = 0

        # Serialize Huffman tree to a bit string
        serialized_tree = self._serialize_huffman_tree(self.huffman_tree)

        with open(input_file_path, 'rb') as infile, open(output_file_path, 'wb') as outfile:
            # Write a placeholder for padding info (1 byte) and tree length (4 bytes)
            outfile.write(b'\x00') # Placeholder for padding
            outfile.write(struct.pack('>I', len(serialized_tree))) # Tree length

            # Write serialized tree to file
            for bit in serialized_tree:
                bit_buffer += bit
                while len(bit_buffer) >= 8:
                    byte = int(bit_buffer[:8], 2)
                    compressed_data.append(byte)
                    bit_buffer = bit_buffer[8:]

            # Write remaining bits of serialized tree
            if bit_buffer:
                # Pad with '0's to make it a full byte
                padding_for_tree = 8 - len(bit_buffer)
                bit_buffer += '0' * padding_for_tree
                byte = int(bit_buffer, 2)
                compressed_data.append(byte)
                bit_buffer = '' # Reset buffer

            # Store padding info for the tree (how many '0's were added)
            outfile.write(struct.pack('>B', padding_for_tree))

            # Write the actual compressed data (from input file)
            infile.seek(0) # Reset file pointer for actual data compression
            while True:
                byte_data = infile.read(1)
                if not byte_data:
                    break
                byte_value = byte_data[0]
                bit_buffer += self.huffman_codes[byte_value]

                while len(bit_buffer) >= 8:
                    byte = int(bit_buffer[:8], 2)
                    compressed_data.append(byte)
                    bit_buffer = bit_buffer[8:]

            # Handle remaining bits (padding)
            if bit_buffer:
                padding_info = 8 - len(bit_buffer)
                bit_buffer += '0' * padding_info
                byte = int(bit_buffer, 2)
                compressed_data.append(byte)

            # Write compressed data to file
            outfile.write(compressed_data)

            # Go back and write the actual padding info for the *data*
            outfile.seek(0)
            outfile.write(struct.pack('>B', padding_info))

        return len(compressed_data)

    def decompress(self, input_file_path, output_file_path):
        with open(input_file_path, 'rb') as infile, open(output_file_path, 'wb') as outfile:
            # Read padding info for data (1 byte)
            padding_info = struct.unpack('>B', infile.read(1))[0]

            # Read tree length (4 bytes)
            serialized_tree_len = struct.unpack('>I', infile.read(4))[0]

            # Read padding info for tree (1 byte)
            padding_for_tree = struct.unpack('>B', infile.read(1))[0]

            # Read serialized tree bits
            tree_bit_string = ''
            bytes_read_for_tree = 0
            while len(tree_bit_string) < serialized_tree_len + padding_for_tree:
                byte_data = infile.read(1)
                if not byte_data:
                    break
                tree_bit_string += format(byte_data[0], '08b')
                bytes_read_for_tree += 1

            # Remove padding from the end of the tree bit string
            tree_bit_string = tree_bit_string[:serialized_tree_len]

            # Deserialize Huffman tree
            tree_string_iter = iter(tree_bit_string)
            self.huffman_tree = self._deserialize_huffman_tree(tree_string_iter)
            self.reverse_huffman_codes = {}
            self._build_huffman_codes(self.huffman_tree, '') # Rebuild codes from deserialized tree

            # Read remaining compressed data
            compressed_bytes = infile.read()
            bit_string = ''
            for byte_value in compressed_bytes:
                bit_string += format(byte_value, '08b')

            # Remove padding from the end of the data bit string
            bit_string = bit_string[:-padding_info] if padding_info > 0 else bit_string

            # Decompress data
            current_code = ''
            current_node = self.huffman_tree
            for bit in bit_string:
                if bit == '0':
                    current_node = current_node.left
                else:
                    current_node = current_node.right

                if current_node.byte is not None:
                    outfile.write(bytes([current_node.byte]))
                    current_node = self.huffman_tree # Reset to root for next byte


class HuffmanGUI:
    def __init__(self, master):
        self.master = master
        master.title("Universal Huffman Compressor")

        self.compressor = HuffmanCompressor()

        # UI Elements
        self.label = tk.Label(master, text="Select a file to compress or decompress:")
        self.label.pack(pady=10)

        self.file_path_entry = tk.Entry(master, width=50)
        self.file_path_entry.pack(pady=5)

        self.browse_button = tk.Button(master, text="Select Any File", command=self._browse_file)
        self.browse_button.pack(pady=5)

        self.compress_button = tk.Button(master, text="Compress", command=self._compress_file)
        self.compress_button.pack(pady=5)

        self.decompress_button = tk.Button(master, text="Decompress", command=self._decompress_file)
        self.decompress_button.pack(pady=5)

        self.result_label = tk.Label(master, text="")
        self.result_label.pack(pady=10)

        self.note_label = tk.Label(master, text="Note: Already compressed files (e.g., JPG, MP4) may not shrink further.", fg="gray")
        self.note_label.pack(pady=5)

    def _browse_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.file_path_entry.delete(0, tk.END)
            self.file_path_entry.insert(0, file_path)

    def _get_file_size(self, file_path):
        size_bytes = os.path.getsize(file_path)
        if size_bytes < 1024:
            return f"{size_bytes} Bytes"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.2f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.2f} MB"

    def _compress_file(self):
        input_file_path = self.file_path_entry.get()
        if not input_file_path:
            messagebox.showerror("Error", "Please select an input file.")
            return

        if not os.path.exists(input_file_path):
            messagebox.showerror("Error", "Input file does not exist.")
            return

        try:
            original_size = os.path.getsize(input_file_path)
            output_file_path = input_file_path + ".huff"
            compressed_size_bytes = self.compressor.compress(input_file_path, output_file_path)

            original_size_formatted = self._get_file_size(input_file_path)
            compressed_size_formatted = self._get_file_size(output_file_path)

            if original_size > 0:
                space_saved_percentage = ((original_size - compressed_size_bytes) / original_size) * 100
            else:
                space_saved_percentage = 0.0 # Handle empty original file

            result_text = (
                f"Compression successful!\n"
                f"Original Size: {original_size_formatted}\n"
                f"Compressed Size: {compressed_size_formatted}\n"
                f"Space Saved: {space_saved_percentage:.2f}%\n"
                f"Output file: {output_file_path}"
            )
            self.result_label.config(text=result_text)
            messagebox.showinfo("Success", result_text)

        except ValueError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during compression: {e}")

    def _decompress_file(self):
        input_file_path = self.file_path_entry.get()
        if not input_file_path:
            messagebox.showerror("Error", "Please select an input file.")
            return

        if not os.path.exists(input_file_path):
            messagebox.showerror("Error", "Input file does not exist.")
            return

        if not input_file_path.endswith(".huff"):
            messagebox.showerror("Error", "Selected file is not a .huff compressed file.")
            return

        try:
            output_file_path = input_file_path.replace(".huff", "_decompressed")
            self.compressor.decompress(input_file_path, output_file_path)

            result_text = (
                f"Decompression successful!\n"
                f"Output file: {output_file_path}"
            )
            self.result_label.config(text=result_text)
            messagebox.showinfo("Success", result_text)

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during decompression: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = HuffmanGUI(root)
    root.mainloop()
