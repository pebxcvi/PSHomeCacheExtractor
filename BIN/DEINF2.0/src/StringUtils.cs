using System;
using System.Data;
using System.Text;

public static class StringUtils
{
    public static byte[] HexStringToByteArray(this string hex)
    {
        string cleanedRequest = hex.Replace(" ", string.Empty).Replace("\n", string.Empty);

        if (cleanedRequest.Length % 2 == 1)
            throw new Exception("[StringUtils] - HexStringToByteArray - The binary key cannot have an odd number of digits");

        byte optMode = 0;
        if (IsLowerCaseHexOnly(cleanedRequest))
            optMode = 2;
        else if (IsUpperCaseHexOnly(cleanedRequest))
            optMode = 1;

        byte[] arr = new byte[cleanedRequest.Length >> 1];

        for (int i = 0; i < cleanedRequest.Length >> 1; ++i)
        {
            arr[i] = (byte)((cleanedRequest[i << 1].GetHexVal(optMode) << 4) + cleanedRequest[(i << 1) + 1].GetHexVal(optMode));
        }

        return arr;
    }

    public static double Eval(this string expression, string filter = null)
    {
        return Convert.ToDouble(new DataTable().Compute(expression, filter));
    }
    
    
    private static bool IsLowerCaseHexOnly(string str)
    {
        foreach (char c in str)
        {
            if (char.IsDigit(c)) continue;
            if (!char.IsLower(c)) return false;
        }
        return true;
    }

    private static bool IsUpperCaseHexOnly(string str)
    {
        foreach (char c in str)
        {
            if (char.IsDigit(c)) continue;
            if (!char.IsUpper(c)) return false;
        }
        return true;
    }
    
    public static string ToHexString(this string str)
    {
        StringBuilder sb = new StringBuilder();

        foreach (byte t in Encoding.UTF8.GetBytes(str))
        {
            sb.Append(t.ToString("X2"));
        }

        return sb.ToString();
    }
}