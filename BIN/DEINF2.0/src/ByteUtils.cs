using System;
using System.Runtime.InteropServices;
#if NETCOREAPP3_0_OR_GREATER
using System.Runtime.Intrinsics.Arm;
using System.Runtime.Intrinsics.X86;
#endif

public static class ByteUtils
{
	
        public static byte[] CombineByteArray(byte[] first, byte[] second)
        {
            bool isfirstNull = first == null;
            bool issecondNull = second == null;

            if (isfirstNull && issecondNull)
                return null;
            else if (issecondNull || second.Length == 0)
            {
                int sizeOfArray = first.Length;
                byte[] copy = new byte[sizeOfArray];
                Array.Copy(first, 0, copy, 0, sizeOfArray);
                return copy;
            }
            else if (isfirstNull || first.Length == 0)
            {
                int sizeOfArray = second.Length;
                byte[] copy = new byte[sizeOfArray];
                Array.Copy(second, 0, copy, 0, sizeOfArray);
                return copy;
            }

            int len1 = first.Length;
            int len2 = second.Length;

            int totalLength = len1 + len2;
#if NET6_0_OR_GREATER
            if (totalLength > Array.MaxLength || totalLength < 0)
#else
            if (totalLength > 0X7FFFFFC7 || totalLength < 0)
#endif
            {
                // Return the first array if total length exceeds limits
                int sizeOfArray = len1;
                byte[] copy = new byte[sizeOfArray];
                Array.Copy(first, 0, copy, 0, sizeOfArray);
                return copy;
            }

            int i = 0;
            int j = 0;

            byte[] resultBytes = new byte[totalLength];

            // Combine first, and second arrays
#if NETCOREAPP3_0_OR_GREATER
            unsafe
            {
                fixed (byte* src1Ptr = first, src2Ptr = second, dstPtr = resultBytes)
                {
#if NET8_0_OR_GREATER
                    if (Avx512F.IsSupported)
                    {
                        for (; i <= len1 - 64; i += 64)
                        {
                            Avx512F.Store(dstPtr + i, Avx512F.LoadVector512(src1Ptr + i));
                        }
                        for (; j <= len2 - 64; j += 64)
                        {
                            Avx512F.Store(dstPtr + len1 + j, Avx512F.LoadVector512(src2Ptr + j));
                        }
                    }
#endif
                    if (Avx.IsSupported)
                    {
                        for (; i <= len1 - 32; i += 32)
                        {
                            Avx.Store(dstPtr + i, Avx.LoadVector256(src1Ptr + i));
                        }
                        for (; j <= len2 - 32; j += 32)
                        {
                            Avx.Store(dstPtr + len1 + j, Avx.LoadVector256(src2Ptr + j));
                        }
                    }
                    if (Sse2.IsSupported)
                    {
                        for (; i <= len1 - 16; i += 16)
                        {
                            Sse2.Store(dstPtr + i, Sse2.LoadVector128(src1Ptr + i));
                        }
                        for (; j <= len2 - 16; j += 16)
                        {
                            Sse2.Store(dstPtr + len1 + j, Sse2.LoadVector128(src2Ptr + j));
                        }
                    }
                    else if (AdvSimd.IsSupported)
                    {
                        for (; i <= len1 - 16; i += 16)
                        {
                            AdvSimd.Store(dstPtr + i, AdvSimd.LoadVector128(src1Ptr + i));
                        }
                        for (; j <= len2 - 16; j += 16)
                        {
                            AdvSimd.Store(dstPtr + len1 + j, AdvSimd.LoadVector128(src2Ptr + j));
                        }
                    }
                }
            }
#endif
            if (i < len1)
                Array.Copy(first, i, resultBytes, i, len1 - i);
            if (j < len2)
                Array.Copy(second, j, resultBytes, len1 + j, len2 - j);

            return resultBytes;
        }
        
        private static readonly uint[] _lookup32Unsafe = CreateLookup32Unsafe();
        private unsafe static readonly uint* _lookup32UnsafeP = (uint*)GCHandle.Alloc(_lookup32Unsafe, GCHandleType.Pinned).AddrOfPinnedObject();

        private static uint[] CreateLookup32Unsafe()
        {
            uint[] result = new uint[256];
            for (int i = 0; i < 256; i++)
            {
                string s = i.ToString("X2");
                if (BitConverter.IsLittleEndian)
                    result[i] = ((uint)s[0]) + ((uint)s[1] << 16);
                else
                    result[i] = ((uint)s[1]) + ((uint)s[0] << 16);
            }
            return result;
        }

    public unsafe static string ToHexString(this Span<byte> bytes)
    {
        uint* lookupP = _lookup32UnsafeP;
        char[] result = new char[bytes.Length * 2];
        fixed (byte* bytesP = bytes)
        fixed (char* resultP = result)
        {
            uint* resultP2 = (uint*)resultP;
            for (int i = 0; i < bytes.Length; i++)
            {
                resultP2[i] = lookupP[bytesP[i]];
            }
        }
        return new string(result);
    }

    public unsafe static string ToHexString(this byte[] bytes)
    {
        uint* lookupP = _lookup32UnsafeP;
        char[] result = new char[bytes.Length * 2];
        fixed (byte* bytesP = bytes)
        fixed (char* resultP = result)
        {
            uint* resultP2 = (uint*)resultP;
            for (int i = 0; i < bytes.Length; i++)
            {
                resultP2[i] = lookupP[bytesP[i]];
            }
        }
        return new string(result);
    }
}